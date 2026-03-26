from agno.os import AgentOS

from agents_team import finance_agent, web_agent, reasoning_finance_team

# --------------------------------------------------
# Playground App
# --------------------------------------------------
agent_os = AgentOS(
    app_id="multi-agent-reasoning-app",
    name="Multi-Agent Reasoning App",
    description=(
        "Interactive playground for a multi-agent financial reasoning system. "
        "Includes financial data analysis, web research, and consolidated reasoning."
    ),
    agents=[
        finance_agent,
        web_agent
    ],
    teams=[reasoning_finance_team]
)

app=agent_os.get_app()

# --------------------------------------------------
# Run Playground
# --------------------------------------------------
if __name__ == "__main__":
    agent_os.serve(
        app="agent_os:app",
        port=7777,
        reload=True
    )