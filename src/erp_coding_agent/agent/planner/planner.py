import json
from typing import Optional
from ...llm.client import LLMClient
from ...llm.models import LLMRequest, Message, Role
from .models import Plan
from ..prompts.planner import PLANNER_SYSTEM_PROMPT

class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def create_plan(self, task: str) -> Optional[Plan]:
        """
        Calls the LLM to generate a structured Plan.
        """
        request = LLMRequest(
            messages=[
                Message(role=Role.SYSTEM, content=PLANNER_SYSTEM_PROMPT),
                Message(role=Role.USER, content=f"Task:\n{task}")
            ],
            response_format={"type": "json_object"}
        )
        
        response = await self.llm.generate(request)
        
        if not response.structured_data:
            return None
            
        try:
            return Plan.model_validate(response.structured_data)
        except Exception as e:
            return None
