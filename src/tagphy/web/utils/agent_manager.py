from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService


class AgentManager:
    def __init__(self, agent: Agent):
        self.session_service = InMemorySessionService()
        self.sessions = {}
        self._runner = Runner(
            agent=agent, app_name="tagphy", session_service=self.session_service
        )

    @property
    def runner(self):
        return self._runner

    def get_session(self, session_id: str):
        return self.sessions[session_id]

    async def create_session(self):
        session = await self.session_service.create_session(
            app_name="tagphy", user_id="tagphy"
        )
        self.sessions[session.id] = session
        return session

    async def delete_session(self, session_id: str):
        session = self.get_session(session_id)
        await self.session_service.delete_session(
            app_name=session.app_name,
            user_id=session.user_id,
            session_id=session.id,
        )
        self.sessions.pop(session_id, None)
