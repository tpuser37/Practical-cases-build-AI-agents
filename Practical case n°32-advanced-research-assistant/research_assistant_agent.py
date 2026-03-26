import os
import requests
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.workflow import Workflow, StepInput, StepOutput
from mistralai import Mistral
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.tools.reasoning import ReasoningTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.knowledge.markdown import MarkdownKnowledgeBase

mistral_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=mistral_key)

MARKDOWN_PATH = "DocumentMarkdown/ocr_document.md"

def create_knowledge_base(markdown_path: str):
    kb = MarkdownKnowledgeBase(
        path=markdown_path,
        vector_db=PgVector(
            table_name="markdown_documents",
            db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        ),
    )
    kb.load(recreate=False)
    return kb

def semantic_scholar_search(query):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query}
    headers = {"x-api-key": "1234567890"}
    response = requests.get(url, params=params, headers=headers)
    return response.json()


summary_agent = Agent(
        name="Summary Agent",
        model=OpenAIChat(id='gpt-4o-mini'),
        instructions=dedent("""
        You are a summary agent designed to summarize the document.
        Read the entire document stored in the knowledge base (in markdown format) and produce a concise summary in plain English. Keep it focused on the paper’s objective, methodology, and key findings.
        """),
        search_knowledge=True,
    )


research_agent = Agent(
        name="Research Agent",
        model=OpenAIChat(id='gpt-4o-mini'),
        instructions=dedent("""
        You are a research assistant designed to simplify and answer questions about academic papers. Your behavior follows this logic:

        1. **Answering Questions**:
        - When a user asks a question, try to answer it using the internal knowledge base first.
        - If you find an answer, cite the **exact source** from the markdown document (quote the relevant sentence or paragraph).
        - Format the answer clearly and showably: include the answer, the citation snippet, and its section or approximate heading if available.

        2. **Fallback to External Tools**:
        - If the knowledge base doesn't contain enough information to answer:
            - Use `semantic_shcolar_search(query)` to look for external answers.
            - If that fails, retry once.
            - If it still fails, use `GoogleSearchTool(query)` as a backup.
        - When using external tools, always show the **source link** or citation (title, author if possible, and source URL).
        - Keep external answers clean, brief, and properly attributed.

        3. **Formatting**:
        - Always use clean markdown formatting.
        - Highlight the **source** of every answer clearly.
        - Avoid hallucinating—if you don’t know, say you’ll look it up.

        Your top priorities are accuracy, traceability (always show the source), and clarity.
        """),
        search_knowledge=True,
        tools=[ReasoningTools(add_instructions=True), semantic_scholar_search, GoogleSearchTools()],
    )

def ocr_step(step_input: StepInput) -> StepOutput:
    pdf_path = step_input.input["pdf_path"]

    uploaded_pdf = client.files.upload(
        file={
            "file_name": pdf_path,
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr",
    )

    signed_url = client.files.get_signed_url(uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=False,
    )

    os.makedirs("DocumentMarkdown", exist_ok=True)

    with open(MARKDOWN_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(page.markdown for page in ocr_response.pages))

    return StepOutput(content={"markdown_path": MARKDOWN_PATH})

def knowledge_base_step(step_input: StepInput) -> StepOutput:
    markdown_path = step_input.previous_step_content["markdown_path"]

    kb = create_knowledge_base(markdown_path)

    return StepOutput(content={"knowledge_base": kb})

def summary_step(step_input: StepInput) -> StepOutput:
    kb = step_input.previous_step_content["knowledge_base"]

    summary_agent.knowledge = kb
    response = summary_agent.run("Summarize the document")

    return StepOutput(
        content={
            "summary": response.content,
            "knowledge_base": kb,
        }
    )

document_workflow = Workflow(
    name="DocumentAnalysisWorkflow",
    steps=[
        ocr_step,
        knowledge_base_step,
        summary_step,
    ],
)

if __name__ == "__main__":

    st.title("📄 Agentic Research Assistant (Agno)")

    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])

    if uploaded_file:
        os.makedirs("DocumentMarkdown", exist_ok=True)
        pdf_path = f"DocumentMarkdown/{uploaded_file.name}"

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        if st.button("Run OCR + Summary"):
            with st.spinner("Processing document..."):
                result = document_workflow.run({"pdf_path": pdf_path})
                

            summary = result.content["summary"]
            kb = result.content["knowledge_base"]

            st.subheader("📌 Summary")
            st.write(summary)

            # inject KB into research agent
            research_agent.knowledge = kb
            st.session_state["research_agent"] = research_agent

            st.success("Document ready for Q&A")
        
        if "research_agent" in st.session_state:
            st.subheader("🔎 Ask a question about the paper")

            question = st.text_input("Your question")

        if st.button("Ask"):
            with st.spinner("Generating answer..."):
                st.session_state["research_agent"].print_response(
                    question,
                    stream=True,
                    show_full_reasoning=True,
                    stream_intermediate_steps=True,
                )
