from tools.summarizer_tool import summarizer_tool
from state import Status


def fallback_answer(input_data):
    answers = []

    for key, value in input_data.items():

        if isinstance(value, dict):

            if "temperature_c" in value and "condition" in value:
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

                result = (
                    f"The current weather in {location} is "
                    f"{condition} with a temperature of "
                    f"{temperature}°C"
                )

                feels_like = value.get("feels_like_c")
                humidity = value.get("humidity_percent")
                wind = value.get("wind_speed_kmh")

                if feels_like is not None:
                    result += f", feeling like {feels_like}°C"

                if humidity is not None:
                    result += f", {humidity}% humidity"

                if wind is not None:
                    result += f", and wind speed of {wind} km/h"

                answers.append(result + ".")

            elif "distance_km" in value:
                answers.append(
                    f"The route from {value.get('origin')} "
                    f"to {value.get('destination')} is "
                    f"{value.get('distance_km')} km and takes "
                    f"approximately {value.get('duration_minutes')} "
                    f"minutes by {value.get('mode', 'driving')}."
                )

            elif "content" in value:
                answers.append(
                    str(value["content"]).strip()
                )

            elif "context" in value:
                answers.append(
                    str(value["context"]).strip()
                )

            else:
                answers.append(str(value))

        else:
            answers.append(str(value).strip())

    return " ".join(
        answer for answer in answers if answer
    )


def extract_direct_text(question):

    question = question.strip()

    prefixes = [
        "summarize this:",
        "summarise this:",
        "summarize:",
        "summarise:",
        "summarize the following:",
        "summarise the following:",
        "give me a summary of:",
        "give me a summary for:"
    ]

    lower_question = question.lower()

    for prefix in prefixes:

        if lower_question.startswith(prefix):

            return question[len(prefix):].strip()

    return ""


def summarizer_node(state):

    step = state.get("active_step")

    if step is None:
        return {
            "error": "Summarizer received no active step."
        }

    output_key = step.output_key

    task_status = dict(
        state.get("task_status", {})
    )

    try:

        # ========================================================
        # FIRST: DIRECT TEXT FROM TOOL INPUT
        # ========================================================

        tool_input = step.tool_input or {}

        text = tool_input.get("text")

        # ========================================================
        # SECOND: DIRECT TEXT FROM USER QUESTION
        # ========================================================

        if not text:

            text = extract_direct_text(
                state.get("question", "")
            )

        # ========================================================
        # THIRD: PREVIOUS TOOL OUTPUTS
        # ========================================================

        input_data = {}

        if text:

            input_data["text"] = text

        else:

            input_keys = tool_input.get(
                "input_keys"
            )

            if input_keys is None:
                input_keys = tool_input.get(
                    "inputs"
                )

            if input_keys is None:
                input_keys = tool_input.get(
                    "keys"
                )

            if input_keys:

                for key in input_keys:

                    task = state.get(
                        "task_status",
                        {}
                    ).get(
                        key,
                        {}
                    )

                    status = task.get(
                        "status"
                    )

                    if (
                        status == Status.COMPLETED
                        or status == "completed"
                    ):

                        if key in state.get(
                            "outputs",
                            {}
                        ):

                            input_data[key] = (
                                state["outputs"][key]
                            )

            else:

                for key, value in state.get(
                    "outputs",
                    {}
                ).items():

                    if key == output_key:
                        continue

                    task = state.get(
                        "task_status",
                        {}
                    ).get(
                        key,
                        {}
                    )

                    status = task.get(
                        "status"
                    )

                    if (
                        status == Status.COMPLETED
                        or status == "completed"
                    ):

                        input_data[key] = value

        # ========================================================
        # VALIDATE INPUT
        # ========================================================

        if not input_data:

            raise ValueError(
                "No text or successful tool outputs are available "
                "for summarization."
            )

        # ========================================================
        # CONVERT TO TEXT
        # ========================================================

        if "text" in input_data:

            text = str(
                input_data["text"]
            ).strip()

        else:

            text_parts = []

            for key, value in input_data.items():

                text_parts.append(
                    f"{key}: {value}"
                )

            text = "\n".join(
                text_parts
            )

        if not text:

            raise ValueError(
                "No text available for summarization."
            )

        # ========================================================
        # CALL SUMMARIZER TOOL
        # ========================================================

        result = None

        try:

            result = summarizer_tool(
                text,
                state.get(
                    "question",
                    ""
                )
            )

        except Exception:

            result = None

        # ========================================================
        # FALLBACK
        # ========================================================

        if not result or not result.strip():

            result = fallback_answer(
                input_data
            )

        # ========================================================
        # FINAL VALIDATION
        # ========================================================

        if not result:

            raise ValueError(
                "Unable to generate a final answer."
            )

        # ========================================================
        # SUCCESS
        # ========================================================

        previous = task_status.get(
            output_key,
            {}
        )

        task_status[output_key] = {
            "status": Status.COMPLETED,
            "retries": previous.get(
                "retries",
                0
            ),
            "error": None
        }

        return {
            "outputs": {
                output_key: result
            },
            "task_status": task_status,
            "active_step": None,
            "error": None
        }

    except Exception as e:

        previous = task_status.get(
            output_key,
            {}
        )

        task_status[output_key] = {
            "status": Status.FAILED,
            "retries": previous.get(
                "retries",
                0
            ),
            "error": str(e)
        }

        return {
            "task_status": task_status,
            "error": str(e)
        }