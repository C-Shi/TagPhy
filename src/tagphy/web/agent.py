from fastapi import APIRouter, Body, HTTPException
from tagphy.agent.photo_finder_agent.agent import root_agent
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
            raise HTTPException(status_code=404, detail="Session not found")

    try:
        response = await agent_manager.run(session.id, message)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    return {"response": response, "session": session.id}
