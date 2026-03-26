from textwrap import dedent
from dotenv import load_dotenv
from agno.workflow import Workflow, StepInput, StepOutput
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.tools.python import PythonTools
from agno.utils.pprint import pprint_run_response
from openai import OpenAI
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os
from fastapi.responses import JSONResponse, FileResponse


load_dotenv()

exa_api_key = "2920b66d-167a-4d9b-91f5-5af466558b3f"
client = OpenAI(
        base_url = "https://api.exa.ai",
        api_key = exa_api_key,
    )
mistral_api_key = "1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"

# Exa search step
def exa_research_step(step_input: StepInput) -> StepOutput:
    product_list = step_input.input["product_list"]
    location = step_input.input["location"]

    completion = client.chat.completions.create(
        model="exa-research",
        messages=[
            {
                "role": "user",
                "content": dedent(f"""
                You are an expert in business procurement research.

                Product List: {product_list}
                Location: {location}

                For each product, list top 3 vendors with:
                - Vendor Name
                - Product Title
                - Price
                - Currency
                - Vendor Website
                - Short Description
                - Minimum Order Quantity
                - Shipping Time
                - Bulk Discounts (if any)

                Return clean markdown.
                """)
            }
        ],
        stream=True,
    )

    full_content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            full_content += chunk.choices[0].delta.content

    return StepOutput(
        content={
            "research_markdown": full_content,
            "location": location,
        }
    )

procurement_agent = Agent(
        name='Procurement Agent',
        model= MistralChat(id="ministral-14b-2512", api_key=mistral_api_key),
        instructions=dedent("""
        You are a procurement analysis agent.

        Your goal is to:
        1. Parse the markdown-formatted research output from Exa.
        2. For each product listed, extract the following fields for each vendor:
            - Product Name
            - Vendor Name
            - Product Title
            - Price (convert to numeric if possible)
            - Currency
            - Vendor Website or Purchase Link
            - Short Product Description
            - Minimum Order Quantity (if available)
            - Shipping Time (if available)
            - Bulk Discounts or Deals (if available)
            - Vendor Location (if mentioned)

        3. After extracting the data, write and execute a Python script that creates a file named `data.csv`
            - Use the standard `csv` module
            - After each product, leave a blank line
            - Make the columns in this order: Product Name, Vendor Name, Product Title, Price, Currency, Bulk Discounts or Deals, Vendor Website, Short Product Description, Minimum Order Quantity, Shipping Time
            - The script should write a header row followed by one row per vendor
            - IMPORTANT: When opening the file, always use encoding='utf-8' in open(), e.g. open('data.csv', 'w', newline='', encoding='utf-8')
            - Then use the PythonTools tool to run the script and save the data
            - Based on the data given, create rows for each data point

        Then:

        4. Analyze the data across all products and vendors.
            - Compare vendors based on pricing, shipping times, minimum quantities, and available deals.
            - Prioritize vendors who:
                - Deliver to the specified location
                - Offer the lowest price for comparable quality
                - Have favorable shipping times or bulk deals
                - Appear reliable (from marketplaces or verified sellers)

        5. Write an executive summary that includes:
            - Recommended vendor(s) per product
            - Reasons for the recommendation (price, location, delivery, etc.)
            - Any noteworthy observations (e.g. big pricing differences, best bundle offers)
            - Optional: Flag any vendors that should be avoided due to missing info or suspicious listings

        IMPORTANT: Use PythonTools to write the extracted data to `data.csv`.
        """),
        expected_output=dedent("""
        The output should include:

        1. 📊 Data Summary:
        - Number of products processed
        - Total vendors compared
        - Location considered for delivery: <city>, <country>
        - Any data quality issues or missing fields (if relevant)

        2. 🏆 Recommendations Per Product:
        For each product (e.g., "Office Chair", "Laptop"), provide:

        ### Product: <Product Name>

        **Recommended Vendor:** <Vendor Business Name>  
        **Price:** <Price and Currency>  
        **Why Chosen:**  
        - Reason 1 (e.g. best price for similar features)
        - Reason 2 (e.g. fastest shipping)
        - Reason 3 (e.g. known/verified vendor or bulk deal)

        **Runner-Up:** <Vendor Business Name>  
        - Mention if relevant (e.g. slightly higher price but faster delivery or better reviews)

        IMPORTANT: Confirm that the CSV file was written as part of this run.
        """),
        tools=[PythonTools()],
        markdown=True
    )

def procurement_analysis_step(step_input: StepInput) -> StepOutput:
    research_markdown = step_input.previous_step_content["research_markdown"]
    location = step_input.previous_step_content["location"]

    response = procurement_agent.run(
        f"""
        Research Data:
        {research_markdown}

        Delivery Location:
        {location}
        """
        ).content

    return StepOutput(
        content={
            "agent_response": response
        }
    )
  
procurement_workflow = Workflow(
    name="ProcurementWorkflow",
    steps=[
        exa_research_step,
        procurement_analysis_step,
    ],
)

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Procurement Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# POST /procure
# -------------------------------------------------
@app.post("/procure")
async def procure(
    product_list: str = Form(...),
    location: str = Form(...)
):
    result = procurement_workflow.run(
        product_list=product_list,
        location=location
    )

    return JSONResponse({
        "markdown": result.content["agent_response"],
        "csv_available": os.path.exists("data.csv")
    })

# -------------------------------------------------
# GET /csv
# -------------------------------------------------
@app.get("/csv")
def download_csv():
    if os.path.exists("data.csv"):
        return FileResponse(
            "data.csv",
            media_type="text/csv",
            filename="data.csv"
        )
    return JSONResponse(
        {"error": "CSV not found"},
        status_code=404
    )