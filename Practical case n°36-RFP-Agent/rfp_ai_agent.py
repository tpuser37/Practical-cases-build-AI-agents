import pygsheets
import pandas as pd
from agno.tools import tool
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.tools.reasoning import ReasoningTools
from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.workflow.workflow import Workflow, Step

gc = pygsheets.authorize(client_secret='client_secret.json')

### Setup Knowledge Base ###
knowledge_base = MarkdownKnowledgeBase(
    path="Markdown/",
    vector_db=PgVector(
        table_name="markdown_documents",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    ),
)

@tool(
    name="read_sheet_as_df",
    description="Read an entire Google Sheets worksheet as a pandas DataFrame.",
    show_result=True,
)
def read_sheet_as_df(sheet_id: str, worksheet_title: str) -> str:
    
    sh = gc.open_by_key(sheet_id)
    wks = sh.worksheet_by_title(worksheet_title)
    df = wks.get_as_df()
    return df.to_json(orient="records")


@tool(
    name="write_df_to_sheet",
    description="Write a DataFrame to a Google Sheets worksheet using the sheet ID.",
    show_result=True,
)
def write_df_to_sheet(
    df_json: str,
    sheet_id: str,
    worksheet_title: str,
    start_cell: list[int] = [1, 1]
) -> str:
    
    df = pd.read_json(df_json)
    sh = gc.open_by_key(sheet_id)
    try:
        wks = sh.worksheet_by_title(worksheet_title)
    except pygsheets.WorksheetNotFound:
        wks = sh.add_worksheet(worksheet_title)
    wks.clear()
    wks.set_dataframe(df, start=tuple(start_cell))
    return f"Successfully wrote DataFrame to worksheet '{worksheet_title}' in sheet '{sheet_id}'."

# --- Step 1: Read Sheet ---
read_step = Step(
    name="read_sheet_step",
    agent=Agent(
        name="Sheet Reader",
        model=OpenAIChat(id="gpt-4o"),
        tools=[read_sheet_as_df],
        instructions="""
        Receive input with keys 'sheet_id' and 'worksheet_title'.
        Call the tool `read_sheet_as_df(sheet_id, worksheet_title)` with these values.
        Return the result as JSON.
        """
    ),
    description="Read the Google Sheet into a JSON DataFrame."
)

# --- Step 2: Fill Missing Fields ---
fill_step = Step(
    name="fill_missing_fields_step",
    agent=Agent(
        name="RFP Filler",
        model=OpenAIChat(id="gpt-4o"),
        tools=[ReasoningTools(add_instructions=True)],
        knowledge=knowledge_base,
        search_knowledge=True,
        instructions="""
        Receive the JSON DataFrame.
        Fill missing values in the 'Response / Answer' column using the company knowledge base.
        Explain each filled field inline using Yes/No/Partial format.
        Return the updated DataFrame as JSON, do not convert to DataFrame outside.
        """
    ),
    description="Fill missing fields using KB and ReasoningTools."
)

# --- Step 3: Validate Answers ---
validate_step = Step(
    name="validate_answers_step",
    agent=Agent(
        name="RFP Validator",
        model=OpenAIChat(id="gpt-4o"),
        tools=[ReasoningTools(add_instructions=True)],
        instructions="""
        Receive the JSON DataFrame from previous step.
        Validate all entries in 'Response / Answer' column follow Yes/No/Partial format.
        Mark inconsistent answers as 'Partial – Needs review'.
        Return validated DataFrame as JSON.
        """
    ),
    description="Validate the filled responses."
)

# --- Step 4: Write Sheet ---
write_step = Step(
    name="write_sheet_step",
    agent=Agent(
        name="Sheet Writer",
        model=OpenAIChat(id="gpt-4o"),
        tools=[write_df_to_sheet],
        instructions="""
        Receive validated JSON DataFrame.
        Convert JSON to pandas DataFrame.
        Write DataFrame back to the Google Sheet, overwriting existing content using write_df_to_sheet() tool.
        """
    ),
    description="Write validated DataFrame back to Google Sheets."
)

rfp_workflow = Workflow(
    name="RFP Completion Workflow",
    description="Multi-step workflow to read, fill, validate, and write RFP sheets.",
    steps=[read_step, fill_step, validate_step, write_step]
)

# --- Example Execution ---
sheet_id = "1Bxyju4NfVG3oMvLnge7FKlxWcn4y8t07Sesr-JaMx9Q"
worksheet_title = "Comprehensive RFP"

rfp_workflow.run({
    "sheet_id": sheet_id,
    "worksheet_title": worksheet_title
})