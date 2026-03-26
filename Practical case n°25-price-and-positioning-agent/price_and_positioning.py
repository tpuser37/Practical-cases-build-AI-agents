from textwrap import dedent
from agno.workflow import Workflow, Step, StepOutput
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.utils.pprint import pprint_run_response
from openai import OpenAI

exa_api_key = "2920b66d-167a-4d9b-91f5-5af466558b3f"
mistral_api_key = "1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"

# ------------------------------
# Custom function for Step 1: Exa research
# ------------------------------
def exa_search_step(step_input) -> StepOutput:
    """Custom function to search top 3 products on Amazon using Exa API."""
    search_term = step_input.input.get("product_details", "")

    client = OpenAI(
        base_url="https://api.exa.ai",
        api_key=exa_api_key,
    )

    completion = client.chat.completions.create(
        model="exa-research",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Find 3 top products matching '{search_term}' on Amazon. "
                    "For each, provide product name, price, short description, and "
                    "3 negative customer reviews mentioning real product complaints."
                ),
            }
        ],
        stream=True,
    )

    full_content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            full_content += chunk.choices[0].delta.content

    # Return as StepOutput to pass to next Agent
    return StepOutput(content=full_content)

# ------------------------------
# Agent: Pricing and Positioning Strategist
# ------------------------------

pricing_and_positioning_strategist = Agent(
        name='Pricing Strategist',
        model= MistralChat(id="ministral-14b-2512", api_key=mistral_api_key),
        instructions=dedent("""
        You are a pricing and product strategy expert.

        You will receive structured market research data about 3 competitor products, including for each:  
        - Competitor name  
        - Price  
        - Product description summary  
        - 3 negative customer reviews highlighting product complaints  

        Your tasks:

        1. Analyze the competitor prices and product positioning (budget, midrange, premium).  
        2. Pay special attention to the competitors’ negative reviews to identify common product issues and customer pain points.  
        3. Based on the competitive pricing landscape and product differentiation, propose a recommended price range for your product:  
        - Classify it as Budget (< $30), Midrange ($30–$50), or Premium (> $50).  
        - Justify why this price range is appropriate, referencing competitors and market conditions.  
        4. Under **Key Competitors**, list each competitor with:  
        - Name and price  
        - A brief note on how it compares to your product  
        - Include the 3 bad reviews associated with that competitor, quoting customer complaints  
        5. Based on the negative reviews, suggest 2–4 tactical recommendations to improve your product and stand out, such as product improvements, bundles, discounts, or unique positioning strategies. Tie each recommendation directly to the competitor complaints you analyzed.
        """),
        expected_output=dedent("""
        Return your output exactly in this markdown format:

        ---

        ## 💰 Recommended Price Range

        **Range**: `$XX – $YY`  
        **Tier**: _Budget / Midrange / Premium_

        ---

        ## 🏷️ Key Competitors

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - _(Add more competitors if applicable)_

        ---

        ## 📊 Rationale

        _Explain why this price range fits your product and market, referencing competitor prices, positioning, and demand._

        ---

        ## 🎯 Tactical Recommendations

        - **[Recommendation 1]**: _Based on competitor complaints, e.g. "Improve pump mechanism to fix frequent failures."_  
        - **[Recommendation 2]**: _E.g. "Offer a cleaning brush bundle addressing cleaning difficulties customers mention."_  
        - _(Add more as relevant)_

        ---

        Keep your analysis specific, actionable, and tied closely to the competitor data and customer feedback.
        """),
        markdown=True
    )

# ------------------------------
# Workflow
# ------------------------------
workflow = Workflow(
    name="ProductPriceAndPositioningWorkflow",
    steps=[
        Step(name="ExaResearch", executor= exa_search_step),
        Step(name="PricingAnalysis", agent= pricing_and_positioning_strategist),
    ]
)
if __name__ == '__main__':
    from rich.prompt import Prompt

    product = Prompt.ask("Enter your product details")
    if product:
        # Run workflow
        response = workflow.run({"product_details": product})
        pprint_run_response(response, markdown=True)