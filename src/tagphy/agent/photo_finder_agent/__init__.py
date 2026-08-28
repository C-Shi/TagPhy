import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from tagphy.agent.photo_finder_agent.agent import root_agent
from tagphy.tools.agent.photo_finder_agent import extract_photo_finder_turn


async def main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="tagphy", user_id="dev")
    runner = Runner(
        agent=root_agent, app_name="tagphy", session_service=session_service
    )

    while True:
        text = input("You: ").strip()
        if text in {"q", "quit", "exit"}:
            break
        events = []
        async for event in runner.run_async(
            user_id="dev",
            session_id=session.id,
            new_message=Content(role="user", parts=[Part.from_text(text=text)]),
        ):
            events.append(event)
            # print tool results / final text as you go
        print(extract_photo_finder_turn(events))


if __name__ == "__main__":
    asyncio.run(main())
