

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class PlanExecute(TypedDict):
    input: str
    plan: list[str]
    past_steps: Annotated[list[tuple], operator.add]
    response: str

class Plan(BaseModel):
    step: list[str] = Field(
        description="需要执行的不同步骤,应该按顺序排列"
    )
