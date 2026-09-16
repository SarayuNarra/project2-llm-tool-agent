from typing import Any, Dict
# ============================================================
# RETRY CONFIGURATION
# ============================================================
MAX_RETRIES = 2
# ============================================================
# ERROR CLASSIFICATION
# ============================================================
def is_retryable_error(error: Exception | str) -> bool:
    """
    Return True only for errors that may succeed if retried.
    Deterministic/input errors should not be retried.
    """
    message = str(error).lower()
    non_retryable_errors = [
        "division by zero",
        "invalid expression",
        "invalid input",
        "missing required",
        "required field",
        "unsupported",
        "not found",
        "clarification_required",
    ]
    for text in non_retryable_errors:
        if text in message:
            return False
    # Network/API/service failures are generally retryable.
    retryable_errors = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "temporary",
        "rate limit",
        "too many requests",
        "service unavailable",
        "server error",
        "502",
        "503",
        "504",
    ]
    for text in retryable_errors:
        if text in message:
            return True
    # Unknown exceptions are treated as non-retryable.
    # This prevents accidental retry loops.
    return False
# ============================================================
# TASK STATUS HELPERS
# ============================================================
def mark_task_running(
    state: Dict[str, Any],
    output_key: str,
) -> Dict[str, Any]:
    task_status = dict(
        state.get("task_status", {})
    )
    previous = task_status.get(
        output_key,
        {}
    )
    task_status[output_key] = {
        "status": "running",
        "retries": previous.get(
            "retries",
            0
        ),
        "error": None,
    }
    return task_status
def mark_task_completed(
    state: Dict[str, Any],
    output_key: str,
) -> Dict[str, Any]:
    task_status = dict(
        state.get("task_status", {})
    )
    previous = task_status.get(
        output_key,
        {}
    )
    task_status[output_key] = {
        "status": "completed",
        "retries": previous.get(
            "retries",
            0
        ),
        "error": None,
    }
    return task_status
def mark_task_failed(
    state: Dict[str, Any],
    output_key: str,
    error: str,
) -> Dict[str, Any]:
    task_status = dict(
        state.get("task_status", {})
    )
    previous = task_status.get(
        output_key,
        {}
    )
    task_status[output_key] = {
        "status": "failed",
        "retries": previous.get(
            "retries",
            0
        ),
        "error": str(error),
    }
    return task_status
# ============================================================
# RETRY HELPERS
# ============================================================
def get_retry_count(
    state: Dict[str, Any],
    output_key: str,
) -> int:
    task_status = state.get(
        "task_status",
        {}
    )
    task = task_status.get(
        output_key,
        {}
    )
    return task.get(
        "retries",
        0
    )
def should_retry(
    state: Dict[str, Any],
    output_key: str,
    error: Exception | str,
) -> bool:
    retries = get_retry_count(
        state,
        output_key
    )
    if retries >= MAX_RETRIES:
        return False
    return is_retryable_error(error)
def mark_task_retry(
    state: Dict[str, Any],
    output_key: str,
    error: Exception | str,
) -> Dict[str, Any]:
    task_status = dict(
        state.get("task_status", {})
    )
    previous = task_status.get(
        output_key,
        {}
    )
    retries = previous.get(
        "retries",
        0
    ) + 1
    task_status[output_key] = {
        "status": "pending",
        "retries": retries,
        "error": str(error),
    }
    return task_status
# ============================================================
# STATUS CHECKS
# ============================================================
def get_task_error(
    state: Dict[str, Any],
    output_key: str,
):
    task_status = state.get(
        "task_status",
        {}
    )
    task = task_status.get(
        output_key,
        {}
    )
    return task.get("error")
def is_task_failed(
    state: Dict[str, Any],
    output_key: str,
) -> bool:
    task_status = state.get(
        "task_status",
        {}
    )
    task = task_status.get(
        output_key,
        {}
    )
    status = task.get("status")
    return str(status).lower() in {
        "failed",
        "status.failed",
    }
def is_task_completed(
    state: Dict[str, Any],
    output_key: str,
) -> bool:
    task_status = state.get(
        "task_status",
        {}
    )
    task = task_status.get(
        output_key,
        {}
    )
    status = task.get("status")
    return str(status).lower() in {
        "completed",
        "status.completed",
    }
def handle_task_failure(
    state,
    output_key,
    error,
):
    task_status = dict(
        state.get("task_status", {})
    )
    previous = task_status.get(
        output_key,
        {}
    )
    retries = previous.get(
        "retries",
        0
    )
    if should_retry(
        state,
        output_key,
        error
    ):
        task_status[output_key] = {
            "status": "failed",
            "retries": retries + 1,
            "error": str(error),
        }
    else:
        task_status[output_key] = {
            "status": "failed",
            "retries": retries,
            "error": str(error),
        }
    return task_status