from fastapi import APIRouter, Body, HTTPException
from tagphy.agent import AgentFactory
from tagphy.web.utils.agent_manager import AgentManager

router = APIRouter(prefix="/agents")

photo_finder_agent = AgentFactory.create_agent(
    agent_type="photo_finder_agent", model="gemini-3.7-flash"
)

photo_finder_agent_manager = AgentManager(photo_finder_agent)


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
        session = await photo_finder_agent_manager.create_session()
    else:
        try:
            session = await photo_finder_agent_manager.get_session(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")

    try:
        response = await photo_finder_agent_manager.run(session.id, message)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    return {"response": response, "session": session.id}


@router.get("/sessions")
async def sessions():
    return await AgentManager.list_all_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    # @TODO: Only one agent at a time is supported for now. This is allowed. Will refactor later when multi agent kick in.
    return await photo_finder_agent_manager.get_session(session_id)
