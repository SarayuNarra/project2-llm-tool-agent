from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from state import AgentState, Status
from schemas.planner_schema import Tool

from nodes.planner import planner_node

from nodes.executor import (
    executor_node,
    get_ready_steps,
)

from nodes.search import search_node
from nodes.calculator import calculator_node
from nodes.summarizer import summarizer_node
from nodes.rag import rag_node
from nodes.weather import weather_node
from nodes.translator import translator_node
from nodes.maps import maps_node
from nodes.response import response_node


# ============================================================
# TOOL NODE REGISTRY
# ============================================================

TOOL_NODES = {
    Tool.SEARCH.value: "search",
    Tool.CALCULATOR.value: "calculator",
    Tool.SUMMARIZER.value: "summarizer",
    Tool.RAG.value: "rag",
    Tool.WEATHER.value: "weather",
    Tool.TRANSLATOR.value: "translator",
    Tool.MAPS.value: "maps",
}


# ============================================================
# DISPATCH READY STEPS
# ============================================================

def dispatch_ready_steps(state):

    sends = []

    for step in state["steps"]:

        output_key = step.output_key

        task = state["task_status"].get(
            output_key,
            {}
        )

        status = task.get("status")

        if status != Status.RUNNING:
            continue

        tool = step.tool

        if isinstance(tool, Tool):
            tool_name = tool.value
        else:
            tool_name = str(tool)

        node_name = TOOL_NODES.get(
            tool_name
        )

        if node_name is None:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        worker_state = dict(state)

        worker_state["active_step"] = step

        sends.append(
            Send(
                node_name,
                worker_state
            )
        )

    if sends:
        return sends

    return "response"


# ============================================================
# INITIAL ROUTER
# ============================================================

def initial_router(state):

    # --------------------------------------------------------
    # NORMAL REQUEST
    # --------------------------------------------------------

    if not state.get("resume", False):
        return "planner"

    # --------------------------------------------------------
    # CONTINUATION REQUEST
    #
    # Skip planner completely.
    # --------------------------------------------------------

    return "executor"


# ============================================================
# BUILD GRAPH
# ============================================================

builder = StateGraph(AgentState)


# ============================================================
# CORE NODES
# ============================================================

builder.add_node(
    "planner",
    planner_node
)

builder.add_node(
    "executor",
    executor_node
)

builder.add_node(
    "response",
    response_node
)


# ============================================================
# TOOL NODES
# ============================================================

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "calculator",
    calculator_node
)

builder.add_node(
    "summarizer",
    summarizer_node
)

builder.add_node(
    "rag",
    rag_node
)

builder.add_node(
    "weather",
    weather_node
)

builder.add_node(
    "translator",
    translator_node
)

builder.add_node(
    "maps",
    maps_node
)


# ============================================================
# START
# ============================================================

builder.add_conditional_edges(
    START,
    initial_router,
    {
        "planner": "planner",
        "executor": "executor",
    }
)


# ============================================================
# PLANNER → EXECUTOR
# ============================================================

builder.add_edge(
    "planner",
    "executor"
)


# ============================================================
# EXECUTOR → TOOLS / RESPONSE
# ============================================================

builder.add_conditional_edges(
    "executor",
    dispatch_ready_steps
)


# ============================================================
# TOOLS → EXECUTOR
# ============================================================

builder.add_edge(
    "search",
    "executor"
)

builder.add_edge(
    "calculator",
    "executor"
)

builder.add_edge(
    "summarizer",
    "executor"
)

builder.add_edge(
    "rag",
    "executor"
)

builder.add_edge(
    "weather",
    "executor"
)

builder.add_edge(
    "translator",
    "executor"
)

builder.add_edge(
    "maps",
    "executor"
)


# ============================================================
# RESPONSE → END
# ============================================================

builder.add_edge(
    "response",
    END
)


# ============================================================
# COMPILE
# ============================================================

graph = builder.compile()