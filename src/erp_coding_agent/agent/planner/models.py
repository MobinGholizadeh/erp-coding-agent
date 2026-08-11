from pydantic import BaseModel, Field
from typing import List

class Step(BaseModel):
    id: int
    description: str
    expected_outcome: str

class Plan(BaseModel):
    steps: List[Step] = Field(description="The sequence of steps to accomplish the task.")
    initial_context_queries: List[str] = Field(
        default_factory=list,
        description="Search queries to gather initial context before starting execution."
    )
