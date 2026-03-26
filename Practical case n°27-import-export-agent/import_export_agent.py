import os
import streamlit as st
from textwrap import dedent
from typing import Iterator
from mistralai import Mistral
from agno.models.mistral import MistralChat
from agno.agent import Agent
from agno.workflow import Workflow, Step, StepOutput
from agno.tools.duckduckgo import DuckDuckGoTools

mistral_key = "1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"

client = Mistral(api_key=mistral_key)

# OCR the pdf and return the text
def ocr_pdf(pdf_path, pdf_name):
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

    with open(f"Documents/{pdf_name}.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))

    return True

def export_law_document(agent, query, num_documents=None, **kwargs):
    with open("Documents/uk-export-law.md", "r") as f:
        export_law_text = f.read()
    return export_law_text

def import_law_document(agent, query, num_documents=None, **kwargs):
    with open("Documents/morocco-import-law.md", "r") as f:
        import_law_text = f.read()
    return import_law_text

translation_agent = Agent(
    name = 'Translation Agent',
    model= MistralChat(id="ministral-14b-2512", api_key=mistral_key),
    instructions = dedent("""
    You are an expert in translation. You are given a text in markdown format in French and you need to translate it to English.
    IMPORTANT: Keep the same structure and content of the original text.
    """),
)

specialist_agent = Agent(
    name = 'Specialist Agent',
    model= MistralChat(id="ministral-14b-2512", api_key=mistral_key),
    instructions = dedent("""
    You are an Export-Import Compliance Expert with access to two knowledge sources:
    - The official UK export law document for electronics (including licences, restrictions, taxes, fees),
    - The official Moroccan import law document for electronics (including permits, quantity limits, import duties, VAT, prohibited items, and customs procedures).

    You also have access to DuckDuckGoTools() to find up-to-date, authoritative data when it is missing or unclear.

    Your task is: given detailed product info (type, quantity, raw materials) and the shipment route (UK to Morocco), provide a **full, precise, step-by-step explanation** of:

    1. **UK export process**:
       - Exact licence requirements by name and code,
       - Clear restrictions on product types or materials,
       - Specific export taxes, fees, or levies with exact amounts or percentages,
       - Necessary documentation, including official form names or codes,
       - Compliance rules and penalties with numbers and legal references.

    2. **Moroccan import process**:
       - Precise import permits and certifications required,
       - Exact quantity restrictions or exemptions,
       - Detailed import duties and VAT rates with percentages or fixed amounts,
       - List of prohibited or restricted items by name and code,
       - Required documents with official titles,
       - Customs clearance steps with timelines and fees.

    Use only **facts and figures extracted from your knowledge base or from live, authoritative sources**. Do not guess or be vague.

    If any data is missing in your knowledge, immediately perform a DuckDuckGoTools() lookup for official government or customs sites and incorporate exact data found.

    Present the response in clear, professional language, with no filler text or disclaimers.

    Provide the output as a flowing narrative, but include concrete numbers, names, codes, and references wherever applicable.

    The goal is to give the user a complete, actionable export-import compliance report with real numbers and official requirements.

    If data is unavailable, explicitly state that you researched and could not find updated official info.
    """),
    expected_output = dedent("""
    ### UK Export Process

    [Explain if an export licence is required for the product. Specify licence type and official code if available.]  
    [Mention any restrictions on product types, raw materials, or dual-use classifications found in the UK export law document.]  
    [Provide specific export taxes or fees applicable, with exact amounts or percentages, citing the document.]  
    [Describe required paperwork and compliance steps before shipment.]

    ### Moroccan Import Process

    [Detail import permits, licences, or certifications required for the product according to the Moroccan import law document.]  
    [State any quantity limits or restrictions, quoting exact figures or thresholds.]  
    [Specify prohibited items or materials mentioned in the document.]  
    [Give import duties and VAT rates with percentages or fixed amounts, as documented.]  
    [List all required customs documents and procedures.]

    ### Taxes and Compliance Details

    [Summarize how taxes and fees are calculated and at which stage (export or import) they apply, based on the findings.]  
    [Explain compliance obligations and potential penalties for non-compliance extracted from the documents.]  
    [Include any additional practical advice referenced in the documents for smooth customs clearance.]

    ### Summary and Recommendations

    [Provide a concise summary of the entire export-import process highlighting key points and actionable next steps based solely on the documents’ contents.]
    """),
    knowledge = None,
    search_knowledge=True,
    knowledge_retriever=[],
    tools = [DuckDuckGoTools()],
)


# =========================
# Workflow Steps
# =========================

def step_ocr(step_input) -> StepOutput:
    """OCR PDFs and save Markdown"""
    ocr_pdf('Documents/uk-export-law.pdf', 'uk-export-law')
    ocr_pdf('Documents/morocco-import-law.pdf', 'morocco-import-law')
    return StepOutput(content="OCR completed successfully")

def step_translate(step_input) -> StepOutput:
    """Translate Moroccan law PDF to English"""
    md_content = import_law_document(None, None, None)
    response = translation_agent.run(md_content)
    with open("Documents/morocco-import-law.md", "w") as f:
        f.write(response.content)
    return StepOutput(content=response.content)
# =========================
# Step pour préparer et exécuter le spécialiste
# =========================
def step_prepare_and_run_specialist(step_input) -> StepOutput:
    """Set retrievers and run specialist agent on product details"""
    # 1. Définir les retrievers
    specialist_agent.knowledge_retriever = [export_law_document, import_law_document]
    
    # 2. Récupérer les détails produits
    product_details = step_input.input.get("product_details", "")
    
    # 3. Exécuter l'agent
    response = specialist_agent.run(product_details)
    
    # 4. Retourner la sortie
    return StepOutput(content=response.content)

workflow = Workflow(
    name="ExportImportWorkflow",
    steps=[
        Step(name="OCR PDFs", executor=step_ocr),
        Step(name="Translate Moroccan Law", executor=step_translate),
        Step(name="Run Specialist Agent", executor=step_prepare_and_run_specialist),
    ]
)

if __name__ == "__main__":
    st.title("Import Export Specialist Multi-Agent System")
    product_details = st.text_input("Enter your product details")

    if st.button("Submit"):
        with st.spinner("Running workflow..."):
            step_input = {"product_details": product_details}
            final_output = workflow.run(step_input)
            st.success("✅ Workflow completed")
            st.markdown(final_output.content)