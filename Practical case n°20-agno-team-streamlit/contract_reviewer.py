import os
import streamlit as st
from agno.team import Team
from textwrap import dedent
from pypdf import PdfReader
from agno.agent import Agent
from agno.models.mistral import MistralChat
import re

st.title("Contract Reviewer")

st.write(
    "This is a tool that uses AI to review contracts and provide insights and suggestions "
    "on their structure, legality, and negotiability."
)
def clean_pdf_text(text):
    # 1. Remplacer les retours à la ligne simples (au milieu d'une phrase) par un espace
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # 2. Supprimer les espaces entre chiffres et ponctuation bizarres
    # Exemple: "3 8 7 , 0 0 0" -> "387,000"
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)

    # 3. Corriger les tirets ou traits insécables qui coupent les mots
    text = re.sub(r'–', '-', text)  # remplacer tirets spéciaux par "-"
    text = re.sub(r'([a-zA-Z])\s+([a-zA-Z])', r'\1\2', text)  # fusion des lettres isolées séparées par des espaces

    # 4. Réduire plusieurs espaces consécutifs à un seul
    text = re.sub(r'\s+', ' ', text)

    # 5. Restaurer les paragraphes (double retour à la ligne)
    text = re.sub(r'\n{2,}', '\n\n', text)

    return text.strip()

uploaded_file = st.file_uploader("Upload a contract", type=["pdf"])
full_text = ""

if uploaded_file:
    reader = PdfReader(uploaded_file)
    raw_text = "".join(page.extract_text() or "" for page in reader.pages)

    if not raw_text:
        st.error("No text found in the contract.")
    else:
        full_text = clean_pdf_text(raw_text)


def get_document():
    return [{
        "content": full_text,
        "meta_data": {
            "source": uploaded_file.name
        }
    }]

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    st.error("La clé MISTRAL_API_KEY n'est pas définie !")
    st.stop()

structure_agent = Agent(
    model=MistralChat(id="ministral-14b-2512", api_key=api_key),
    name = 'Structure Agent',
    role = 'Contract Structuring Expert',
    instructions = dedent(
        """
        You are a Contract Structuring Expert. Your role is to evaluate the structure of a contract and suggest improvements or build a proper structure from scratch if not provided.
        You will use the tool get_document to retrieve the full contract text.
        Your task is to analyze the contract and determine if it is structured in a clear, complete, and legally appropriate way.
        You must identify missing or unclear sections.
        If a contract is missing structure, suggest a full structure using standard section headers (e.g., Definitions, Terms, Obligations, Termination, Governing Law, etc.).
        Avoid legal interpretation, focus only on organization, clarity, and logical flow.
        Be concise but clear in your analysis.
        Output a markdown-style structure if creating a new structure, or bullet-pointed comments if evaluating an existing one.
        """
    ),
    tools = [get_document],
    markdown = True,
   
)

legal_agent = Agent(
    model=MistralChat(id="ministral-14b-2512", api_key=api_key),
    name = 'Legal Agent',
    role = 'Legal issue Analyst',
    instructions = dedent(
        """
        You are a Legal Framework Analyst tasked with identifying legal issues, risks, and key legal principles in the uploaded contract.
        Use the 'get_document' tool to access the full contract text. For every legal issue or observation, you MUST:

        — Quote the exact clause, sentence, or paragraph from the contract that your point is based on.
        — Start a new line with 'Issue:' followed by a short, clear explanation of the legal concern or principle.
        — Clearly refer to the section title, heading, or paragraph number if available. If not, describe its location.
        — DO NOT make any legal assessment or comment unless it is directly supported by a quote from the contract.

        Your task:
        — Identify the legal domain of the contract (e.g., commercial law, employment, NDA, etc.)
        — Determine the likely jurisdiction or applicable law
        - Highlight any potential legal issues or problematic clauses

        Format each finding as follows:

        Clause:
        "Quoted contract text here."
        Section: [Section title or location]
        Issue:
        Your brief analysis of why this clause may present a legal concern.
        """
    ),
    tools = [get_document],
    markdown = True,
)

negotiate_agent = Agent(
    model=MistralChat(id="ministral-14b-2512", api_key=api_key),
    name='Negotiation Agent',
    role='Contract Negotiation Strategist',
    instructions=dedent("""
        You are a Contract Negotiation Strategist.
        Your job is to identify parts of a contract that are commonly negotiable or potentially unbalanced.

        You MUST:
        — Always quote the exact paragraph or clause you're referring to.
        — Clearly explain why it may be negotiable or needs adjustment.
        — Suggest a counter-offer or alternative phrasing.

        Structure your analysis like this:

        1. **Quoted Clause** (Exact text from the contract)

        2. **Why it is negotiable or problematic**

        3. **Example strategy or counter-suggestion**
                
        Do NOT make general comments. Every point you make must be backed by a direct quote from the contract, and your output must clearly show which part you are referring to.
"""),
    tools=[get_document],
    markdown=True,
)

manager_agent = Team(
    members=[structure_agent, legal_agent, negotiate_agent],
    model=MistralChat(id="ministral-14b-2512", api_key=api_key),
    instructions = dedent("""
    You are the lead summarizer. You must combine input from:
    1. Legal Agent
    2. Structure Agent
    3. Negotiation Agent

    Key Requirements:
    - For all legal and negotiation points, preserve quoted clauses from the contract as evidence.
    - The Legal Agent should highlight specific legal issues, followed by a short 'Issue:' explanation.
    - Each quoted excerpt must be followed by the agent's explanation or recommendation.
    - Remove redundant or unclear comments and make the output clean and easy to follow.
    - Ensure that all bullet points in Strengths and Gaps/Recommendations are on separate lines, with a line break after each item.
    - Do NOT include any legal issues or negotiation suggestions unless they are directly justified by a clause extracted from the uploaded document. 
    If a clause does not exist in the document, do NOT include the point in the output.

    Output Format:
    1. ### Executive Summary
    - A brief paragraph (~4 lines) summarizing the contract, its purpose, parties, and key points.

    2. ### Legal Context
    - List each legal issue as a bullet point:
        - **Title of the issue**
        - Clause: "Quoted contract text here"
        - Issue: Explanation of the legal concern
    - Only include issues with clauses directly quoted from the document.
    - Only include legal issues that are directly justified by a quoted clause from the uploaded contract.
    - Do NOT include general legal risk summaries or jurisdictional statements unless they are explicitly supported by a clause quote.
    - Skip any point where a supporting clause cannot be extracted.


    3. ### Contract Structure Feedback
    - Include bullet points for structural analysis:
        - Strengths:
            - Each strength on a separate line.
        - Gaps / Recommendations:
            - Each recommendation on a separate line.

    4. ### Negotiation Recommendations
    - For each negotiable point, display:
        - **Title of the recommendation** (no clause number)
        - Clause: "Quoted text from the contract — must be directly extracted from the uploaded document"
        - Suggestion: Start with a verb, e.g., "Propose a 30-day notice period", "Consider adjusting the payment terms", etc.
    - IMPORTANT: Only include points that are justified by clauses extracted from the document. Do NOT invent any clauses.
    - Do NOT display any negotiation recommendation if there is no clause directly supporting it in the uploaded document.
    - You MUST Only include legal issues or negotiation suggestions that are fully supported by an exact quoted clause from the document.
    - Do NOT generate placeholder text such as "No clause found" or any invented issues.
    - For each negotiable point, display:
        - **Title of the recommendation** (no clause number)
        - Clause: "Quoted text from the contract — must be directly extracted from the uploaded document"
        - Suggestion: Start with a verb, e.g., "Propose a 30-day notice period", "Consider adjusting the payment terms", etc.
        - IMPORTANT: Only include points that are justified by clauses extracted from the document. 
    - Do NOT invent any clauses. 
    - Do NOT write anything like "No existing clause" or "Not found in the document". 
    - If a clause does not exist in the document, skip that point entirely.


""")
)

if uploaded_file and full_text:
    if st.button("Analyze Contract"):
        with st.spinner("Generating analysis..."):
            try:
                # Exécute le Team manager_agent
                team_output = manager_agent.run(
                    "Please review and summarize the uploaded contract."
                )
                
                # Extraire le texte brut de l'objet TeamRunOutput
                output_text = getattr(team_output, "content", str(team_output))
                
                # Affiche le résultat dans Streamlit
                st.subheader("Contract Analysis Output")
                st.markdown(output_text)
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse du contrat : {e}")

else:
    st.info("Upload a PDF contract to start the analysis.")
