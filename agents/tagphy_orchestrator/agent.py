from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="tagphy_orchestrator",
    description="Coordinates TagPhy agents.",
    instruction="You orchestrate TagPhy. Sub-agents and tools will be added later.",
)
