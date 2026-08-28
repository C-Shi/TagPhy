import time
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from tagphy.tools.agent.photo_finder_agent import extract_photo_finder_turn


class AgentManager:
    def __init__(self, agent: Agent):
        self.session_service = InMemorySessionService()
        self._sessions = {}
        self._runner = Runner(
            agent=agent, app_name="tagphy", session_service=self.session_service
        )

    def get_session(self, session_id: str):
        return self._sessions[session_id].get("session")

    async def run(self, session_id: str, message: str):
        session = self._sessions[session_id]
        if (
            session["last_request_time"]
            and time.time() - session["last_request_time"] < 5
        ):
            raise ValueError("Too many requests in the last 5 seconds")
        session["total_requests_count"] += 1
        if session["total_requests_count"] > 30:
            await self.delete_session(session_id)
            raise ValueError(
                "You have reached the maximum number of requests for this session. Session deleted. Please create a new session."
            )
        events = []
        async for event in self._runner.run_async(
            user_id="tagphy",
            session_id=session_id,
            new_message=Content(role="user", parts=[Part.from_text(text=message)]),
        ):
            events.append(event)
        session["last_request_time"] = time.time()
        return extract_photo_finder_turn(events)

    async def create_session(self):
        session = await self.session_service.create_session(
            app_name="tagphy", user_id="tagphy"
        )
        self._sessions[session.id] = {
            "session": session,
            "total_requests_count": 0,
            "last_request_time": None,
        }
        return session

    async def delete_session(self, session_id: str):
        session = self._sessions[session_id].get("session")
        await self.session_service.delete_session(
            app_name=session.app_name,
            user_id=session.user_id,
            session_id=session.id,
        )
        self._sessions.pop(session_id, None)
