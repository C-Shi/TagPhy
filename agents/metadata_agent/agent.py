from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="metadata_agent",
    description="Extracts photo EXIF metadata.",
    instruction="Extract EXIF date, device, and GPS. Implementation comes later.",
)
