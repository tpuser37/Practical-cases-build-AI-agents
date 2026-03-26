import os
import asyncio
import pandas as pd
from uqlm import BlackBoxUQ
from uqlm.utils import load_example_dataset, math_postprocessor
from langchain_openai import ChatOpenAI
from agno.agent import Agent
from agno.models.mistral import MistralChat


api_key=os.getenv("MISTRAL_API_KEY")
async def main():
    # Load dataset
    svamp = load_example_dataset("svamp", n=5)

    # Prompting
    MATH_INSTRUCTION = (
        "When you solve this math problem only return the final numeric answer.\n"
    )
    prompts = [MATH_INSTRUCTION + q for q in svamp.question]

    # LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # UQLM
    bbuq = BlackBoxUQ(llm=llm)
    results = await bbuq.generate_and_score(prompts)
    df = results.to_df()

    # Postprocess math outputs
    if "response" in df.columns:
        df["processed_output"] = df["response"].apply(math_postprocessor)
    elif "generation" in df.columns:
        df["processed_output"] = df["generation"].apply(math_postprocessor)
    else:
        raise ValueError("No output column found")

    # ✅ TRUE AGNO AGENT
    hallucination_agent = Agent(
        name="HallucinationDetector",
        role="Detect hallucinations in math answers",
        instructions="""
You are a verification agent.

Input:
- Math question
- Model answer
- Uncertainty score

Decide if the answer is hallucinated.

Rules:
- If answer is not numeric → HALLUCINATION
- If answer is logically inconsistent → HALLUCINATION
- If uncertainty > 0.5 and reasoning seems weak → HALLUCINATION
- Otherwise → OK

Respond only with:

DECISION: OK or HALLUCINATION
REASON: short explanation
""",
        model=MistralChat(api_key=api_key, id="mistral-medium-2508")
    )

    # Run hallucination detection
    decisions = []
    reasons = []

    for i, row in df.iterrows():
        question = svamp["question"][i]
        answer = row["processed_output"]
        uncertainty = row.get("uncertainty", None)

        agent_input = f"""
Question:
{question}

Answer:
{answer}

Uncertainty:
{uncertainty}
"""

        verdict = await hallucination_agent.arun(agent_input)
        verdict_text = verdict.content

        decisions.append(
            "HALLUCINATION" in verdict_text
        )
        reasons.append(verdict_text)

    df["hallucination"] = decisions
    df["hallucination_reason"] = reasons

    # Final view
    print("\n========== FINAL RESULTS ==========")
    print(
        df[
            [
                "processed_output",
                "uncertainty",
                "hallucination",
                "hallucination_reason",
            ]
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
