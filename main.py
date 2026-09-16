from graph import graph

conversation_state = None
pending_clarification = None

def create_initial_state(question):
    return {
        "question": question,
        "steps": [],
        "outputs": {},
        "task_status": {},
        "active_step": None,
        "answer": "",
        "error": None,
        "ready_steps": [],
        "resume": False,
    }

def get_answer(result):
    answer = result.get("answer")
    if answer:
        return str(answer)
    outputs = result.get("outputs", {})
    if "final_answer" in outputs:
        return str(outputs["final_answer"])
    if len(outputs) == 1:
        return str(next(iter(outputs.values())))
    if outputs:
        return str(outputs)
    return "I could not generate an answer."

def find_clarification(result):
    outputs = result.get("outputs", {})
    for key, value in outputs.items():
        if not isinstance(value, dict):
            continue
        if value.get("status") == "clarification_required":
            return {
                "output_key": key,
                "location": value.get(
                    "location",
                    ""
                ),
                "message": value.get(
                    "message",
                    ""
                ),
                "candidates": value.get(
                    "candidates",
                    []
                ),
            }
    return None


def get_selected_location(
    user_input,
    candidates,
):
    user_input = user_input.strip()

    if user_input.isdigit():
        index = int(user_input)
        if 1 <= index <= len(candidates):
            return candidates[index - 1]
        return None

    if user_input:
        return user_input
    return None

def update_maps_step(
    state,
    clarification,
    selected_location,
):
    output_key = clarification["output_key"]
    ambiguous_location = str(
        clarification.get(
            "location",
            ""
        )
    ).strip().lower()
    updated_steps = []
    for step in state.get("steps", []):
        if step.output_key != output_key:
            updated_steps.append(step)
            continue
        tool_input = dict(
            step.tool_input or {}
        )
        origin = str(
            tool_input.get(
                "origin",
                ""
            )
        ).strip()

        destination = str(
            tool_input.get(
                "destination",
                ""
            )
        ).strip()

        if origin.lower() == ambiguous_location:

            tool_input["origin"] = selected_location

        elif destination.lower() == ambiguous_location:

            tool_input["destination"] = selected_location

        elif (
            ambiguous_location
            and ambiguous_location in origin.lower()
        ):

            tool_input["origin"] = selected_location

        elif (
            ambiguous_location
            and ambiguous_location in destination.lower()
        ):

            tool_input["destination"] = selected_location

        if "mode" not in tool_input:

            tool_input["mode"] = "driving"

        updated_step = step.model_copy(
            update={
                "tool_input": tool_input
            }
        )

        updated_steps.append(
            updated_step
        )

    return updated_steps


def prepare_continuation(
    state,
    clarification,
    selected_location,
):
    """
    Prepare the existing plan for continuation.

    Only the ambiguous Maps location is changed.
    The existing plan is preserved.
    """

    output_key = clarification["output_key"]

    updated_steps = []

    for step in state.get("steps", []):

        if step.output_key != output_key:
            updated_steps.append(step)
            continue

        tool_input = dict(step.tool_input or {})

        ambiguous_location = (
            clarification.get("location", "")
            .strip()
            .lower()
        )

        origin = str(
            tool_input.get("origin", "")
        ).strip()

        destination = str(
            tool_input.get("destination", "")
        ).strip()

        if origin.lower() == ambiguous_location:
            tool_input["origin"] = selected_location

        elif destination.lower() == ambiguous_location:
            tool_input["destination"] = selected_location

        tool_input["mode"] = "driving"

        updated_step = step.model_copy(
            update={
                "tool_input": tool_input
            }
        )

        updated_steps.append(updated_step)

    task_status = dict(
        state.get("task_status", {})
    )

    previous = task_status.get(
        output_key,
        {}
    )

    task_status[output_key] = {
        "status": "pending",
        "retries": previous.get("retries", 0),
        "error": None,
    }

    outputs = dict(
        state.get("outputs", {})
    )

    outputs.pop(output_key, None)

    for step in updated_steps:

        if output_key not in step.depends_on:
            continue

        dependent_key = step.output_key

        old = task_status.get(
            dependent_key,
            {}
        )

        task_status[dependent_key] = {
            "status": "pending",
            "retries": old.get("retries", 0),
            "error": None,
        }

        outputs.pop(
            dependent_key,
            None
        )

    continuation_state = dict(state)

    continuation_state["steps"] = updated_steps
    continuation_state["task_status"] = task_status
    continuation_state["outputs"] = outputs
    continuation_state["active_step"] = None
    continuation_state["answer"] = ""
    continuation_state["error"] = None
    continuation_state["ready_steps"] = []
    continuation_state["resume"] = True

    return continuation_state

def run_agent(user_input):

    global conversation_state
    global pending_clarification

    user_input = user_input.strip()

    if not user_input:
        return "Please enter a request."

    if pending_clarification is not None:

        clarification = pending_clarification

        candidates = clarification.get(
            "candidates",
            []
        )

        selected_location = get_selected_location(
            user_input,
            candidates
        )

        if not selected_location:

            return (
                "Please select a valid option number "
                "or enter the location name."
            )

        if conversation_state is None:

            pending_clarification = None

            return (
                "The previous clarification context "
                "was lost. Please submit the request again."
            )

        continuation_state = prepare_continuation(
            conversation_state,
            clarification,
            selected_location
        )

        try:

            result = graph.invoke(
                continuation_state
            )

        except Exception as exc:

            conversation_state = continuation_state

            pending_clarification = clarification

            return (
                f"Unable to continue the request: {exc}"
            )

        new_clarification = find_clarification(
            result
        )

        if new_clarification:

            conversation_state = result

            pending_clarification = (
                new_clarification
            )

            return new_clarification["message"]


        if result.get("error"):

            conversation_state = result

            pending_clarification = clarification

            return get_answer(result)

        conversation_state = None
        pending_clarification = None

        return get_answer(result)

    initial_state = create_initial_state(
        user_input
    )

    try:

        result = graph.invoke(
            initial_state
        )

    except Exception as exc:

        return (
            f"Unable to process the request: {exc}"
        )

    clarification = find_clarification(
        result
    )

    if clarification:

        conversation_state = result

        pending_clarification = clarification

        return clarification["message"]

    conversation_state = None
    pending_clarification = None

    return get_answer(result)

if __name__ == "__main__":

    print()
    print(
        "================================================"
    )
    print(
        "          AI ENGINEER TOOL AGENT"
    )
    print(
        "================================================"
    )
    print(
        "Type 'exit' to quit."
    )
    print()

    while True:

        try:

            user_input = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\nGoodbye!"
            )

            break

        if user_input.lower() == "exit":

            print(
                "\nGoodbye!"
            )

            break

        if not user_input:
            continue

        answer = run_agent(
            user_input
        )

        print()
        print("Agent:")
        print(answer)
        print()