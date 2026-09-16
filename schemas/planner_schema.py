from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class Tool(str, Enum):
    SEARCH = "search"
    CALCULATOR = "calculator"
    SUMMARIZER = "summarizer"
    RAG = "rag"
    WEATHER = "weather"
    TRANSLATOR = "translator"
    MAPS = "maps"

class Step(BaseModel):
    tool: Tool
    tool_input: dict[str, Any]
    output_key: str
    depends_on: list[str] = Field(
        default_factory=list
    )
    is_final: bool = False

class PlannerOutput(BaseModel):
    steps: list[Step]