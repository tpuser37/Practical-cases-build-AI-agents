import os
from agno.agent import Agent
from agno.team import Team
from agno.models.mistral import MistralChat
from agno.db.sqlite import SqliteDb  # classique, pas Async
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.reasoning import ReasoningTools

api_key="1kA2D1feYkVIJODPXYd2df3NYcnHK4oI"
db = SqliteDb(db_file="tmp/agents_system.db")


# --------------------------------------------------
# Web Search Agent
# --------------------------------------------------
web_agent = Agent(
    name="Web Research Agent",
    role="Handle web search requests and general financial research",
    model=MistralChat(api_key=api_key, id="mistral-medium-2508"),
    tools=[DuckDuckGoTools()],
    db=db,
    instructions=[
        "Search for current and relevant information on financial topics.",
        "Always include sources and publication dates.",
        "Focus on reputable financial news sources.",
        "Provide context and background information."
    ],
    enable_agentic_memory=True,
    add_datetime_to_instructions=True,
    markdown=True,
    add_history_to_context=True,
)

# --------------------------------------------------
# Finance Data Agent
# --------------------------------------------------
finance_agent = Agent(
    name="Finance Agent",
    role="Handle financial data requests and market analysis",
    model=MistralChat(api_key=api_key, id="mistral-medium-2508"),
    tools=[
        YFinanceTools(
            stock_price= True,
            company_info= True,
            key_financial_ratios= True,
            analyst_recommendations=True,
        )
    ],
    db=db,
    instructions=[
        "You are a financial data specialist.",
        "Generate accurate and structured financial reports.",
        "Use tables to display stock prices, P/E, market cap, and revenue.",
        "Clearly state the company name and ticker.",
        "Include key financial ratios in your analysis.",
        "Focus on actionable financial insights.",
        "Tasks may run in parallel if needed."
    ],
    enable_agentic_memory=True,
    add_datetime_to_instructions=True,
    markdown=True,
    add_history_to_context=True,
)

# --------------------------------------------------
# Reasoning Finance Team
# --------------------------------------------------
reasoning_finance_team = Team(
    name="Reasoning Finance Team",
    model=MistralChat(api_key=api_key, id="mistral-medium-2508"),
    team_id="reasoning_finance_team",
    members=[web_agent, finance_agent],
    tools=[ReasoningTools(add_instructions=True)],
    db=db,

    instructions=[
        "Provide consolidated financial and investment insights.",
        "Combine quantitative analysis with market sentiment.",
        "Support all claims with data and cited sources.",
        "Use tables and charts when relevant.",
        "Present results in a structured and easy-to-follow format.",
        "Only output the final consolidated analysis.",
        "Do not expose individual agent responses.",
        "Do not use emojis."
    ],
    success_criteria=(
        "The team has provided a complete financial analysis "
        "including data, visualizations, risks, and actionable "
        "investment recommendations."
    ),
    enable_agentic_context=True,
    enable_agentic_memory=True,
    add_datetime_to_instructions=True,
    markdown=True
)
