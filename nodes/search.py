from tools.search_tool import search_tool
from state import Status
from utils.error_handling import should_retry
def search_node(state):
    step = state["active_step"]
    output_key = step.output_key
    query = step.tool_input.get("query")
    task_status = dict(state["task_status"])
    previous = task_status.get(
        output_key,
        {}
    )
    retries = previous.get(
        "retries",
        0
    )
    try:
        # --------------------------------------------------
        # Execute search tool
        # --------------------------------------------------
        result = search_tool(query)
        task_status[output_key] = {
            "status": Status.COMPLETED,
            "retries": retries,
            "error": None,
        }
        return {
            "outputs": {
                output_key: result
            },
            "task_status": task_status,
            "error": None,
        }
    except Exception as e:
        error_message = str(e)
        # --------------------------------------------------
        # Retry temporary failures
        # --------------------------------------------------
        if should_retry(
            state,
            output_key,
            error_message
        ):
            task_status[output_key] = {
                "status": Status.PENDING,
                "retries": retries + 1,
                "error": error_message,
            }
        else:
            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": error_message,
            }
        return {
            "task_status": task_status,
            "error": error_message,
        }