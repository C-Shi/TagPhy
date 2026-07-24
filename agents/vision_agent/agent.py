from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="vision_agent",
    description="Tags photos and matches entities.",
    instruction="Tag images. Implementation comes later.",
)
