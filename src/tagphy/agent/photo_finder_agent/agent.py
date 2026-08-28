from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from tagphy.tools.agent.photo_finder_agent import *


def tool_rank_photos(tool_context: ToolContext) -> dict:
    """Rank photos and return a fixed search_results payload for the UI gallery.

    Returns dict with type=search_results, query, and items (id, description,
    preview_url, similarity). Call only when you are ready to show matches.
    Do not invent ids or URLs in chat text — the UI reads this tool result.
    """
    description = tool_context.state.get("search_query") or ""
    tags = tool_context.state.get("tags") or []
    tag_ids = get_candidate_tags(tags)
    photos = get_candidate_photos_ids(tag_ids)
    photo_ids = [photo["id"] for photo in photos]
    return rank_photos(description, photo_ids)


def tool_update_search_context(
    tool_context: ToolContext, description: str, tags: list[str]
) -> None:
    """Update the search query in session state.
    Args:
        description: The combined, refineddescription of the photo from current and all previous turns
        tags: A dictionary of tags that best match the described photo. Tags selection pool come from `get_all_tags` tool.
    """
    tool_context.state["search_query"] = description
    tool_context.state["tags"] = tags


def system_prompt(context):
    return f"""
        You are a helpful assistant that finds potential photos based on a user's description of the photo.
        If user ask anything else than finding photos, you should politely decline and say you are not able to help with that. Then describe what you can do instead
        User may include other information that is no related to the photo, such as greeting message. You should extract the core photo description from the user's description.
        User may or may not describe the photo clearly. Ask question to clarify what the target photo looks like if you are unsure about. If you are sure, proceed to the next step.
        In each turn, you should ONLY call each tool once. If you need to call a tool multiple times, that means you need to interact with
        You should always have potential tags to look for. If you could not find any potential tags, you should ask the user to provide more information unitl you are able to locate at least one tag.

        When user asks for a photo, you should always start with the following steps:
        You have access to the following tools:
            - get_all_tags: Get all tags from the database
            - tool_rank_photos: Rank photos based on a user's description of the photo
            - tool_update_search_context: Update the search query in session state. Call it with each turn

        Response format (important for the UI):
        - Clarifying questions, declines, and greetings: reply in natural language only.
          Do NOT call tool_rank_photos on those turns.
        - When you have enough detail and want to show matches: call tool_rank_photos.
          The tool returns the structured result (ids + preview_url) the UI uses for thumbnails.
          In chat, you may add at most one short sentence (e.g. "Here are the closest matches.").
          Do NOT paste JSON, invent photo ids, or invent preview URLs in your text.

        Your workflow is as follows:
        1. Use `get_all_tags` tool to obtain the current list of image tags from database
        2. Examinate the query user provided. From tag_lists, pick up to 3 most relevant tags. You will need both id and name of the tags
        3. Call tool_update_search_context with the combined, refined description and the tags you picked up
        4. Use `tool_rank_photos` tool to rank the photos
        5. Optionally add a short free-text caption; do not restate the structured list in JSON

        Muti-turn rule:
        You maintain one running photo description in session state: search_query.
        When the user describes or refines the photo:
        1. Read the current search_query (if any).
        2. Mentally merge their NEW message into a SINGLE updated description:
        - Add new details (place, color, who, when).
        - If they correct something ("not cat, dog"), REPLACE that part; do not keep both.
        - Drop chit-chat ("hi", "sorry", "not those") from the description.
        3. Call tool_update_search_context with the FULL updated description (not only the new words).
        4. Then continue search tools / rank using that saved query.
        Never pass a partial phrase like only "sofa" or only "dog" as the whole search_query
        unless that is truly the entire description so far.

    """


root_agent = Agent(
    model="gemini-3.5-flash",
    name="photo_finder_agent",
    description="An agent that finds potential photos based on a user's description of the photo",
    instruction=system_prompt,
    tools=[
        get_all_tags,
        tool_rank_photos,
        tool_update_search_context,
    ],
)
