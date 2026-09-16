from typing import Annotated
from typing_extensions import TypedDict
from enum import Enum
from schemas.planner_schema import Step
# ==================================================
# TASK STATUS
# ==================================================
class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
# ==================================================
# MERGE DICTIONARIES
# ==================================================
def merge_dicts(left: dict, right: dict) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged
# ==================================================
# MERGE ERRORS
# ==================================================
def merge_errors(left, right):
    """
    Safely merge error values coming from
    parallel tool branches.
    None means no error.
    If one branch has an error, preserve it.
    If both have errors, combine them.
    """
    if left is None:
        return right
    if right is None:
        return left
    if left == right:
        return left
    return f"{left}; {right}"
# ==================================================
# AGENT STATE
# ==================================================
class AgentState(TypedDict):
    question: str
    steps: list[Step]
    outputs: Annotated[
        dict,
        merge_dicts
    ]
    task_status: Annotated[
        dict,
        merge_dicts
    ]
    active_step: Step | None
    answer: str
    error: Annotated[
        str | None,
        merge_errors
    ]
    ready_steps: list[Step]
    resume: bool