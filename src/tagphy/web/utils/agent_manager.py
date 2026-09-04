from google.adk import Agent, Runner
from google.adk.sessions import DatabaseSessionService, Session
from google.genai.types import Content, Part

from tagphy.tools.agent.photo_finder_agent import extract_photo_finder_turn
from tagphy import app_root

db_url = f"sqlite+aiosqlite:///{app_root()}/agent.db"


class AgentManager:
    def __init__(self, agent: Agent):
        self.session_service = DatabaseSessionService(db_url=db_url)
        self._user_id = agent.name
        self._runner = Runner(
            agent=agent, app_name="tagphy", session_service=self.session_service
        )

    @classmethod
    async def list_all_sessions(cls) -> list[Session]:
        session_service = DatabaseSessionService(db_url=db_url)
        return await session_service.list_sessions(app_name="tagphy")

    async def get_session(self, session_id: str):
        return await self.session_service.get_session(
            app_name="tagphy", user_id=self._user_id, session_id=session_id
        )

    async def run(self, session_id: str, message: str):
        events = []
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=Content(role="user", parts=[Part.from_text(text=message)]),
        ):
            events.append(event)
        return extract_photo_finder_turn(events)

    async def create_session(self):
        session = await self.session_service.create_session(
            app_name="tagphy", user_id=self._user_id
        )
        return session

    async def delete_session(self, session_id: str):
        session = await self.get_session(session_id)
        await self.session_service.delete_session(
            app_name=session.app_name,
            user_id=session.user_id,
            session_id=session.id,
        )

    async def list_agent_sessions(self):
        return await self.session_service.list_sessions(
            app_name="tagphy", user_id=self._user_id
        )
