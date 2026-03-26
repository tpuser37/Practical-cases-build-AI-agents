import os
import base64
from dotenv import load_dotenv
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIChat
from agno.workflow import Workflow, StepInput, StepOutput
from freight_agent import full_response

load_dotenv()

# message agent
def get_product_specifications(message):
    """
    Retourne un texte avec seulement les Product Specifications
    à partir du message texte ou image.
    """
    image_data = None

    if isinstance(message, dict):
        with open(message.get("image_path"), "rb") as f:
            image_data = f.read()
        message = message.get("caption", "")

    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""
        If an image is given, identify the product clearly.
        Output ONLY:
        - Product name
        - Dimensions
        - Weight (if inferable)
        - Material
        - Packaging assumptions
        Do NOT ask questions.
        """,
    )

    if image_data:
        response = agent.run(
            message,
            images=[Image(content=image_data)]
        )
    else:
        response = agent.run(message)

    return f"""
User Question:
{message}

Product Specifications:
{response.content}
"""
# --- Step 1 : Product Specs ---
def product_spec_step(step_input: StepInput) -> StepOutput:
    message = step_input.input["message"]
    product_specs = get_product_specifications(message)
    return StepOutput(content={"product_specs": product_specs})

# --- Step 2 : Freight Agent ---
def freight_step(step_input: StepInput) -> StepOutput:
    product_specs = step_input.previous_step_content["product_specs"]
    freight_answer = full_response(product_specs)
    return StepOutput(content={"freight_answer": freight_answer})

# --- Workflow ---
whatsapp_freight_workflow = Workflow(
    name="WhatsAppFreightWorkflow",
    steps=[
        product_spec_step,
        freight_step,
    ],
)

if __name__ == '__main__':
    print(get_product_specifications('hello'))