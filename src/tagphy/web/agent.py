from fastapi import APIRouter, Body
from google.genai.types import Content, Part
from tagphy.agent.photo_finder_agent.agent import root_agent
from tagphy.tools.agent.photo_finder_agent import extract_photo_finder_turn
from tagphy.web.utils.agent_manager import AgentManager

router = APIRouter(prefix="/api/agent")

agent_manager = AgentManager(root_agent)


@router.post("/photo-finder")
async def photo_finder(
    message: str = Body(
        ..., embed=True, description="The message to send to the agent"
    ),
    session_id: str | None = Body(
        embed=True,
        description="The session id to use for the agent",
        default=None,
    ),
):
    if session_id is None:
        session = await agent_manager.create_session()
    else:
        try:
            session = agent_manager.get_session(session_id)
        except KeyError:
            # silently create a new session should the previous session is not found to smooth user experience
            session = await agent_manager.create_session()

    events = []
    async for event in agent_manager.runner.run_async(
        user_id="tagphy",
        session_id=session.id,
        new_message=Content(role="user", parts=[Part.from_text(text=message)]),
    ):
        events.append(event)
    response = extract_photo_finder_turn(events)
    return {"response": response, "session": session.id}
