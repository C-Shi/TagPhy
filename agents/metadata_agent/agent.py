from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from tagphy.tools.image_processor import ImageProcessor

def extract_metadata(image_path: str, tool_context: ToolContext) -> dict:
    """Extracts metadata from an image.
    Args:
        image_path: The path to the image.
    Returns:
        A dictionary containing the metadata.
    """
    processor = ImageProcessor()
    try:
        metadata = processor.extract_metadata(image_path)
        tool_context.state["year_taken"] = metadata["year"]
        tool_context.state["location"] = metadata["location"]
        return { **metadata, "status": "success" }
    except Exception as e:
        tool_context.state["year_taken"] = None
        tool_context.state["location"] = None
        return { "status": "error", "year": None, "location": None }


system_instruction = """
    You are a metadata agent. You are given a file path to an image and you need to extract the metadata from the image. 
    rules:
      - You are required to use `extract_metadata` tool
      - You are required to extract the year taken and the location from the image.
      - Your output to shows the metadata return by the tool.
      - If you find the year_taken or location is None, that is OK. Do not invent any values
"""
root_agent = Agent(
    model="gemini-3.1-flash-lite",
    name="metadata_agent",
    description="Extracts photo EXIF metadata.",
    instruction=system_instruction,
    tools=[extract_metadata]
)
