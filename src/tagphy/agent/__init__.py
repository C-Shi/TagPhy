from typing import Literal
from google.adk.agents import Agent

from tagphy.agent.photo_finder_agent.agent import create_photo_finder_agent

AGENT_TYPES = Literal["photo_finder_agent"]


class AgentFactory:
    @staticmethod
    def create_agent(agent_type: AGENT_TYPES, model: str = None) -> Agent:
        if agent_type == "photo_finder_agent":
            return create_photo_finder_agent(model)
