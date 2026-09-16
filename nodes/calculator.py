import re

from tools.calculator_tool import calculator_tool

from state import Status

from utils.error_handling import should_retry


def extract_number_from_text(text):
    """
    Extract a likely numerical value from unstructured text.

    Handles:
        1,493,475,196
        1493475196
        75,760.96
        75.76
        1.49 billion
        1.49 million
    """

    if not isinstance(text, str):
        return None

    # Prefer numbers containing commas.
    comma_numbers = re.findall(
        r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b",
        text
    )

    if comma_numbers:
        return float(
            comma_numbers[0].replace(",", "")
        )

    # Handle values such as:
    # 1.49 billion
    # 123 million
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(billion|million|thousand)\b",
        text,
        re.IGNORECASE
    )

    if match:
        number = float(match.group(1))
        unit = match.group(2).lower()

        multiplier = {
            "billion": 1_000_000_000,
            "million": 1_000_000,
            "thousand": 1_000,
        }[unit]

        return number * multiplier

    # Plain decimal/integer fallback.
    numbers = re.findall(
        r"\b\d+(?:\.\d+)?\b",
        text
    )

    if numbers:
        return float(numbers[0])

    return None


def resolve_dependency_value(
    dependency_key,
    outputs
):
    """
    Resolve a calculator dependency from previous
    tool outputs.
    """

    value = outputs.get(dependency_key)

    if value is None:
        raise ValueError(
            f"Dependency '{dependency_key}' "
            "has no output."
        )

    # Already numeric
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value

    # Structured search output
    if isinstance(value, dict):

        content = value.get("content", "")

        number = extract_number_from_text(
            content
        )

        if number is not None:
            return number

    # Plain text output
    if isinstance(value, str):

        number = extract_number_from_text(
            value
        )

        if number is not None:
            return number

    raise ValueError(
        f"Could not extract a numerical value "
        f"from dependency '{dependency_key}'."
    )


def resolve_expression(
    expression,
    step,
    outputs
):
    """
    Replace dependency names in the calculator
    expression with their resolved numerical values.
    """

    if not isinstance(expression, str):
        raise ValueError(
            "Calculator expression must be a string."
        )

    resolved_expression = expression

    for dependency in step.depends_on:

        value = resolve_dependency_value(
            dependency,
            outputs
        )

        resolved_expression = re.sub(
            rf"\b{re.escape(dependency)}\b",
            str(value),
            resolved_expression
        )

    return resolved_expression


def calculator_node(state):

    step = state["active_step"]

    output_key = step.output_key

    expression = step.tool_input.get(
        "expression"
    )

    outputs = state.get(
        "outputs",
        {}
    )

    task_status = dict(
        state["task_status"]
    )

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
        # Resolve previous tool outputs
        # --------------------------------------------------

        resolved_expression = resolve_expression(
            expression,
            step,
            outputs
        )

        # --------------------------------------------------
        # Execute calculator
        # --------------------------------------------------

        result = calculator_tool(
            resolved_expression
        )

        # Convert whole-number floats to integers
        # for cleaner output.
        if (
            isinstance(result, float)
            and result.is_integer()
        ):
            result = int(result)

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