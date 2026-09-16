from llm import planner_llm
from prompts.planner_prompt import build_planner_prompt
from nodes.planner_validator import validate_plan
from schemas.planner_schema import Step, Tool


def get_tool_descriptions():
    return """
- search: Search the web for current or external information.
- calculator: Perform mathematical calculations.
- summarizer: Summarize or shorten text provided by the user, or summarize outputs from previous tools.
- rag: Answer questions using documents uploaded by the user.
- weather: Get current weather information for a location.
- translator: Translate text into the requested language.
- maps: Find routes and directions between locations.
"""


def planner_node(state):

    question = state["question"].strip()

    # ============================================================
    # DIRECT SUMMARIZATION
    # ============================================================
    # If the user directly asks to summarize text, do not depend
    # on the planner LLM to construct the summarizer step.
    # ============================================================

    lower_question = question.lower()

    summary_prefixes = (
        "summarize this:",
        "summarise this:",
        "summarize:",
        "summarise:",
        "summarize the following:",
        "summarise the following:",
        "give me a summary of:",
        "give me a summary for:",
    )

    if lower_question.startswith(summary_prefixes):

        prefix = next(
            prefix
            for prefix in summary_prefixes
            if lower_question.startswith(prefix)
        )

        text = question[len(prefix):].strip()

        if not text:
            return {
                "steps": [],
                "task_status": {},
                "active_step": None,
                "ready_steps": [],
                "error": "No text was provided for summarization."
            }

        step = Step(
            tool=Tool.SUMMARIZER,
            tool_input={
                "text": text
            },
            output_key="final_answer",
            depends_on=[],
            is_final=True
        )

        return {
            "steps": [step],
            "task_status": {
                "final_answer": {
                    "status": "pending",
                    "retries": 0,
                    "error": None
                }
            },
            "active_step": None,
            "ready_steps": [],
            "error": None
        }

    # ============================================================
    # NORMAL PLANNER
    # ============================================================

    try:

        tool_descriptions = get_tool_descriptions()

        prompt = build_planner_prompt(
            question,
            tool_descriptions
        )

        plan = planner_llm.invoke(prompt)


        if plan is None:
            raise ValueError(
                "Planner returned no result."
            )

        if not hasattr(plan, "steps"):
            raise ValueError(
                "Planner response does not contain steps."
            )

        if not plan.steps:
            raise ValueError(
                "Planner returned an empty plan."
            )

        validated_steps = validate_plan(
            plan.steps
        )

        if not validated_steps:
            raise ValueError(
                "Planner validation produced no executable steps."
            )

        task_status = {}

        for step in validated_steps:

            task_status[step.output_key] = {
                "status": "pending",
                "retries": 0,
                "error": None
            }

        return {
            "steps": validated_steps,
            "task_status": task_status,
            "active_step": None,
            "ready_steps": [],
            "error": None
        }

    except Exception as e:

        return {
            "steps": [],
            "task_status": {},
            "active_step": None,
            "ready_steps": [],
            "error": f"Planner failed: {str(e)}"
        }