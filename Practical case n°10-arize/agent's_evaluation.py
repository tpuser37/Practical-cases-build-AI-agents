import os
import pandas as pd
from agno.agent import Agent
from agno.models.mistral import MistralChat


api_key="1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"
MODEL_ID = "mistral-medium-2508"
### Setup Tracing

from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.agno import AgnoInstrumentor

# Setup OpenTelemetry via our convenience function
tracer_provider = register(
    space_id="U3BhY2U6MzUyMjU6ZmV2Vg==",
    api_key="ak-e06e7318-8c1b-41cb-aacb-b74e4789c3ea-c_dRyukXzHQ4AkRbpv23InbZBJDaw2qw",
    project_name="the-policy-agent",
)

# Start instrumentation
AgnoInstrumentor().instrument(tracer_provider=tracer_provider)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

from textwrap import dedent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools

# Define the policy research agent
policy_research_agent = Agent(
    model=MistralChat(api_key=api_key, id="mistral-medium-2508"),
    tools=[DuckDuckGoTools(), Newspaper4kTools()],
    description=dedent("""\
        You are a senior agricultural policy analyst who advises the UK government on
        farming, land management and rural development. Your expertise spans: 🌾

        • UK agricultural legislation and subsidy frameworks (post-Brexit)
        • Environmental Land Management Schemes (ELMS)
        • Sustainable farming practices and biodiversity
        • Rural economy and farm business management
        • Food security and supply chain resilience
        • Climate change adaptation in agriculture
        • International trade agreements affecting UK farming\
    """),
    instructions=dedent("""\
        1. Research Phase 🔍
           – Gather comprehensive data from DEFRA, NFU, academic institutions,
             and agricultural research bodies.
           – Focus on latest policy developments and funding schemes.
           – Track changes in farming practices and environmental regulations.

        2. Impact Analysis 📊
           – Evaluate effects of current policies on farm incomes and productivity.
           – Assess environmental outcomes and biodiversity metrics.
           – Monitor rural community wellbeing and economic indicators.

        3. Policy Recommendations ✍️
           – Develop evidence-based proposals for sustainable farming.
           – Balance economic viability with environmental protection.
           – Consider regional variations and farm-type specific needs.

        4. Quality Assurance ✓
           – Verify all statistics and policy details with official sources.
           – Cross-reference with local farming communities' feedback.
           – Identify potential implementation challenges.
    """),
    expected_output=dedent("""\
        # {UK Agricultural Policy Analysis} 🌾

        ## Executive Summary
        {Concise overview of current agricultural landscape and key challenges}

        | Region | Farm Types | Key Issues | Support Schemes |
        |--------|------------|------------|-----------------|
        | England| ...        | ...        | ...            |
        | Wales  | ...        | ...        | ...            |
        | ...    | ...        | ...        | ...            |

        ## Key Findings
        - **Environmental Impact:** {...}
        - **Economic Viability:** {...}
        - **Rural Development:** {...}

        ## Market Analysis
        {Current trends in UK farming and international trade implications}

        ## Recommendations
        1. **Immediate Actions:** {...}
        2. **Mid-term Strategy:** {...}
        3. **Long-term Vision:** {...}

        ## Data Sources
        {Numbered list of references with dates and relevance}

        ---
        Prepared by Agricultural Policy Analyst · Published: {current_date} · Last Updated: {current_time}
    """),
    markdown=True,
)

# Step 1: Get the response from the agent
user_input = "Analyze the current state and future implications of UK agricultural policies and their impact on farming communities"

print("Generating policy analysis...")
print("="*80)

# Show the beautiful formatted output first
print("AGENT OUTPUT:")
print("-" * 40)
policy_research_agent.print_response(user_input, stream=False)
print("-" * 40)

# Now capture the content for evaluation
print("\nCapturing response for evaluation...")
response = policy_research_agent.run(user_input)
actual_output = response.content if hasattr(response, 'content') else str(response)

print("\n" + "="*50)
print("ANALYSIS GENERATED")
print("="*50)
print(actual_output)

evaluation_agent = Agent(
    model=MistralChat(api_key=api_key, id=MODEL_ID),
    description="You are an evaluation agent that assesses policy analyses.",
    instructions=dedent("""
        Evaluate whether the provided policy analysis is impactful.

        Criteria:
        - Covers economic, environmental, and social impacts
        - Mentions farming communities explicitly
        - Provides insights or recommendations
        - Structured and clear

        Output STRICTLY in JSON format:

        {
          "label": "impactful" | "not impactful",
          "explanation": "short step-by-step reasoning"
        }
    """),
    markdown=False
)

evaluation_prompt = f"""
INPUT QUESTION:
{user_input}

ANALYSIS GENERATED:
{actual_output}

EXPECTED FORMAT:
{policy_research_agent.expected_output}
"""

print("\nRunning evaluation...\n")

eval_response = evaluation_agent.run(evaluation_prompt)
eval_text = eval_response.content if hasattr(eval_response, "content") else str(eval_response)

print("===== AGENT 2 EVALUATION =====")
# Nettoyer le JSON généré par l'agent
cleaned_eval_text = eval_text.strip()
import re

cleaned_eval_text = re.sub(r"^```(json)?", "", cleaned_eval_text, flags=re.IGNORECASE)
cleaned_eval_text = re.sub(r"```$", "", cleaned_eval_text)
print(cleaned_eval_text)

from datetime import datetime, timezone

# =============================
# SAVE TO CSV
# =============================
df = pd.DataFrame([{
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "input": user_input,
    "analysis_output": actual_output,
    "evaluation_with_explanation": cleaned_eval_text,
    "model_used": MODEL_ID
}])

output_file = "policy_analysis_mistral_evaluation.csv"
df.to_csv(output_file, index=False)

print("\n✅ RESULTS SAVED")
print(f"File: {output_file}")