import os
import streamlit as st
from textwrap import dedent
from mistralai import Mistral
from agno.workflow import Workflow, Step, StepOutput
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.tools.duckduckgo import DuckDuckGoTools


mistral_key = "1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"

client = Mistral(api_key=mistral_key)

# OCR the pdf and return the text
def ocr_pdf(pdf_path):
    # check if the file exists
    if not os.path.exists(pdf_path):
        st.error("PDF file not found")
        return
    
    uploaded_pdf = client.files.upload(
        file={
            "file_name": pdf_path,
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )

    with open("ocr_response.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))

    return ocr_response.pages

# Custom function to prepare full context for first step
def prepare_context_step(step_input) -> StepOutput:
    ocr_text = step_input.input.get("ocr_text", "")
    
    full_context = f"""
        OCR TEXT:
        {ocr_text}
        """
    return StepOutput(content=full_context)

def research_prompt_step(step_input) -> StepOutput:
    user_country = step_input.input.get("user_country", "")
    summary_text = step_input.previous_step_content  # c'est la sortie du step précédent

    prompt = f"""
        You are a research agent. You are given the structured summary of a document.
        Your task is to generate a similar report focused on COUNTRY: {user_country}.
        Follow the same structure and headings as in the input:

        {summary_text}
"""
    return StepOutput(content=prompt)

structure_and_analysis_agent = Agent(
        name = 'Structure and Analysis Agent',
        model=MistralChat(id="ministral-14b-2512", api_key=mistral_key),
        instructions = dedent("""
        You are an intelligent document analysis agent. You are given the raw text of a PDF (OCR processed). Your task is to analyze the content and produce a structured summary of the document’s subject, key points, and organization. The report discusses a specific country, which you must identify.
        Follow these steps:

        1. Detect and clearly state the COUNTRY being discussed (call this "Country X").
        2. Identify the MAIN TOPIC of the document (e.g. energy policy, health care reforms, education quality).
        3. Define the DOCUMENT STRUCTURE as a clean numbered outline with sections and subsections based on the logical flow of the text.
        4. Extract the KEY ENTITIES, KEY FIGURES (if any), and any important ORGANIZATIONS or AGENCIES mentioned.
        5. Summarize the KEY POINTS and INSIGHTS under each major section, focusing on the data, trends, problems, or conclusions made about Country X.

        Output format:

        COUNTRY: <Country X>
        TOPIC: <main subject of the document>

        STRUCTURE:
        1. <Section Title>
        - <Summary or bullet points>
        2. <Section Title>
        - <Summary or bullet points>
        ...

        KEY POINTS AND INSIGHTS:
        - Bullet points summarizing major findings, arguments, statistics, etc.
        - Must reflect what is emphasized in the document
        - Keep this detailed but concise

        This output will be used by a second agent to replicate a similar report for a different country. Be clear, complete, and well-structured.
        """),
    )

research_agent = Agent(
        name = 'Research Agent',
        model= MistralChat(id="ministral-14b-2512", api_key=mistral_key),
        instructions = dedent(f"""
        You are a research agent. You are given a structured summary of a document about a topic in a specific country. Your task is to generate a new report on the **same topic** but focused on the country provided by the workflow.

        You may use the DuckDuckGoTools() tool to search for real-world information related to Country.

        Instructions:

        1. Read the input summary carefully. It contains:
        - COUNTRY: <Country X>
        - TOPIC: <Main Topic>
        - STRUCTURE: <Numbered outline of the report>
        - KEY POINTS AND INSIGHTS from the original document

        2. Understand the structure and content focus. Your output must use **the same section headings** and address **the same themes**, but for the country provided by the workflow.

        3. For each section, use DuckDuckGoTools() to find reliable and up-to-date information specific to Country provided by the workflow. For example:
        - Local policies
        - Trends
        - Statistics
        - Institutional efforts
        - Challenges and opportunities
        - Relevant events

        4. Rebuild the report using the exact structure, now filled with data and insights from the country provided by the workflow. The tone, depth, and organization should match the original as closely as possible.

        Output format:

        TITLE: <Same topic> in <Country provided by the workflow>

        1. <Section Title from original>
        - <Findings related to the country>
        2. <Next Section>
        - <Continue same structure>

        Cite or refer to sources found via search where helpful.

        IMPORTANT: You must always stay exactly within the subject defined in the original document. Do not go broader, do not narrow the scope, and do not add or remove themes. Reproduce the same structure and content areas, adapted only to the country provided by the workflow . Nothing more, nothing less.
        """),
        tools=[DuckDuckGoTools()],
        )

workflow = Workflow(
    name="ResearchAnalystWorkflow",
    steps=[
        Step(name="PrepareContext", executor= prepare_context_step),
        Step(name="StructureAnalysis", agent= structure_and_analysis_agent),
        Step(name="PrepareResearchPrompt", executor= research_prompt_step),
        Step(name="ResearchGeneration", agent=research_agent),
    ]
)

# Main function
if __name__ == "__main__":
    ocr_text = ""
    user_country = ""
    pdf_path = ""
    st.title("Research Analyst Multi-Agent System")
    with st.form("input_form"):
        pdf_path = st.file_uploader("Upload a PDF file", type=["pdf"])
        user_country = st.text_input("Enter your desired research country")
        submitted = st.form_submit_button("Submit")
    if submitted and pdf_path and user_country:
        with st.spinner("Processing PDF..."):
            # save the pdf locally
            with open(f'UploadedPDF/{pdf_path.name}', "wb") as f:
                f.write(pdf_path.read())
            st.success("PDF file uploaded successfully")
            ocr_pdf(f'UploadedPDF/{pdf_path.name}')
            # read the ocr_response.md file
            with open("ocr_response.md", "r") as f:
                ocr_text = f.read()
            st.success("OCR completed successfully")
        with st.spinner("Running research workflow..."):
            output_placeholder = st.empty()
            full_output = ""
            # Run the workflow and stream the output
            response = workflow.run({"ocr_text": ocr_text, "user_country": user_country})
            if response.content:
                    full_output += response.content
                    output_placeholder.markdown(full_output)
    else:
        st.write("No PDF file uploaded")