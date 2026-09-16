from state import Status
# ============================================================
# GET READY STEPS
# ============================================================
def get_ready_steps(state):
    ready_steps = []
    for step in state["steps"]:
        output_key = step.output_key
        task = state["task_status"].get(
            output_key,
            {}
        )
        status = task.get("status")
        # ----------------------------------------------------
        # Already completed
        # ----------------------------------------------------
        if status == Status.COMPLETED:
            continue
        # ----------------------------------------------------
        # Already running
        # ----------------------------------------------------
        if status == Status.RUNNING:
            continue
        # ----------------------------------------------------
        # Failed tasks are stopped here.
        # Retry handling will be added separately.
        # ----------------------------------------------------
        if status == Status.FAILED:
            continue
        # ----------------------------------------------------
        # Check dependencies
        # ----------------------------------------------------
        dependencies_completed = True
        for dependency in step.depends_on:
            dependency_status = (
                state["task_status"]
                .get(dependency, {})
                .get("status")
            )
            if dependency_status != Status.COMPLETED:
                dependencies_completed = False
                break
        if dependencies_completed:
            ready_steps.append(step)
    return ready_steps
# ============================================================
# EXECUTOR NODE
# ============================================================
def executor_node(state):
    ready_steps = get_ready_steps(state)
    if not ready_steps:
        return {}
    task_status = dict(
        state["task_status"]
    )
    for step in ready_steps:
        output_key = step.output_key
        previous = task_status.get(
            output_key,
            {}
        )
        task_status[output_key] = {
            "status": Status.RUNNING,
            "retries": previous.get(
                "retries",
                0
            ),
            "error": None,
        }
    return {
        "task_status": task_status
    }