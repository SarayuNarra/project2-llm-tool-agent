from state import Status


# ============================================================
# FORMAT STRUCTURED TOOL OUTPUT
# ============================================================

def format_output(value):

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    if isinstance(value, dict):

        if (
            "temperature_c" in value
            and "condition" in value
        ):

            location = value.get(
                "location",
                "the requested location"
            )

            condition = value.get(
                "condition",
                "unknown"
            )

            temperature = value.get(
                "temperature_c"
            )

            feels_like = value.get(
                "feels_like_c"
            )

            humidity = value.get(
                "humidity_percent"
            )

            wind = value.get(
                "wind_speed_kmh"
            )

            answer = (
                f"The current weather in {location} is "
                f"{condition} with a temperature of "
                f"{temperature}°C"
            )

            if feels_like is not None:
                answer += (
                    f", feeling like {feels_like}°C"
                )

            if humidity is not None:
                answer += (
                    f", with {humidity}% humidity"
                )

            if wind is not None:
                answer += (
                    f" and wind speed of {wind} km/h"
                )

            return answer + "."

        # ----------------------------------------------------
        # MAPS
        # ----------------------------------------------------

        if (
            "distance_km" in value
            and "duration_minutes" in value
        ):

            origin = value.get(
                "origin",
                "the origin"
            )

            destination = value.get(
                "destination",
                "the destination"
            )

            distance = value.get(
                "distance_km"
            )

            duration = value.get(
                "duration_minutes"
            )

            mode = value.get(
                "mode",
                "driving"
            )

            return (
                f"The route from {origin} to "
                f"{destination} is approximately "
                f"{distance} km and takes around "
                f"{duration} minutes by {mode}."
            )

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        if (
            "title" in value
            and "content" in value
        ):

            return str(
                value["content"]
            ).strip()

        # ----------------------------------------------------
        # RAG
        # ----------------------------------------------------

        if "context" in value:

            return str(
                value["context"]
            ).strip()

    # --------------------------------------------------------
    # NORMAL VALUES
    # --------------------------------------------------------

    return str(value).strip()


# ============================================================
# RESPONSE NODE
# ============================================================

def response_node(state):

    outputs = state.get(
        "outputs",
        {}
    )

    steps = state.get(
        "steps",
        []
    )

    task_status = state.get(
        "task_status",
        {}
    )

    final_answer = ""

    # ========================================================
    # CHECK FOR CLARIFICATION
    # ========================================================

    for key, value in outputs.items():

        if not isinstance(value, dict):
            continue

        if value.get(
            "status"
        ) != "clarification_required":
            continue

        message = value.get(
            "message",
            "I need more information to complete your request."
        )

        return {
            "answer": message,
            "error": None
        }

    # ========================================================
    # FIND FINAL ANSWER
    # ========================================================

    for step in steps:

        if not step.is_final:
            continue

        final_output = outputs.get(
            step.output_key
        )

        if final_output is not None:

            final_answer = format_output(
                final_output
            )

            break

    # ========================================================
    # FIND FAILED / SKIPPED TASKS
    # ========================================================

    failed_tasks = []
    skipped_tasks = []

    for key, task in task_status.items():

        status = task.get(
            "status"
        )

        status_string = str(
            status
        ).lower()

        if (
            status == Status.FAILED
            or status_string
            in {
                "failed",
                "status.failed"
            }
        ):

            failed_tasks.append(
                (
                    key,
                    task.get(
                        "error",
                        "Unknown error"
                    )
                )
            )

        elif (
            status == Status.SKIPPED
            or status_string
            in {
                "skipped",
                "status.skipped"
            }
        ):

            skipped_tasks.append(
                (
                    key,
                    task.get(
                        "error",
                        "Skipped because a dependency failed"
                    )
                )
            )

    # ========================================================
    # NORMAL SUCCESS
    # ========================================================

    if final_answer and not failed_tasks:

        return {
            "answer": final_answer,
            "error": None
        }

    # ========================================================
    # PARTIAL SUCCESS
    # ========================================================

    if outputs:

        response_parts = []

        response_parts.append(
            "I completed some parts of your request, "
            "but one or more tasks failed."
        )

        response_parts.append("")

        # ----------------------------------------------------
        # Successful outputs
        # ----------------------------------------------------

        for key, value in outputs.items():

            if key == "final_answer":
                continue

            if (
                isinstance(value, dict)
                and value.get(
                    "status"
                ) == "clarification_required"
            ):
                continue

            response_parts.append(
                format_output(value)
            )

        # ----------------------------------------------------
        # Failed tasks
        # ----------------------------------------------------

        if failed_tasks:

            response_parts.append("")

            response_parts.append(
                "Some tasks failed:"
            )

            for key, error in failed_tasks:

                response_parts.append(
                    f"- {key}: {error}"
                )

        # ----------------------------------------------------
        # Skipped tasks
        # ----------------------------------------------------

        if skipped_tasks:

            response_parts.append("")

            response_parts.append(
                "Some tasks were skipped because "
                "their dependencies failed:"
            )

            for key, error in skipped_tasks:

                response_parts.append(
                    f"- {key}: {error}"
                )

        return {
            "answer": "\n".join(
                response_parts
            ),
            "error": (
                failed_tasks[0][1]
                if failed_tasks
                else None
            )
        }

    # ========================================================
    # COMPLETE FAILURE
    # ========================================================

    if failed_tasks:

        response_parts = [
            "I couldn't complete your request.",
            "",
            "Some tasks failed:"
        ]

        for key, error in failed_tasks:

            response_parts.append(
                f"- {key}: {error}"
            )

        if skipped_tasks:

            response_parts.append("")

            response_parts.append(
                "Dependent tasks were skipped:"
            )

            for key, error in skipped_tasks:

                response_parts.append(
                    f"- {key}: {error}"
                )

        return {
            "answer": "\n".join(
                response_parts
            ),
            "error": failed_tasks[0][1]
        }

    # ========================================================
    # NOTHING AVAILABLE
    # ========================================================

    return {
        "answer": "I could not generate an answer.",
        "error": state.get(
            "error"
        )
    }