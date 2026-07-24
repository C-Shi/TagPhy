from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="storage_agent",
    description="Moves tagged photos and updates the database.",
    instruction="Move files then update DB paths. Implementation comes later.",
)
