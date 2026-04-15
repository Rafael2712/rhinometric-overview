"""
Assertion evaluator service.

Evaluates a list of ServiceAssertion rules against a health-check result.
Called from health_checker._check_one() after the connector returns a response.

Responsibilities:
  - Evaluate each enabled assertion in order
  - Return structured results (pass/fail, actual, expected, error)
  - Simple dot-notation JSON path parsing (no external dependencies)
  - Graceful error handling (eval error = fail, never crash the check)

v1 assertion types:
  - status_code      : HTTP status must equal expected value
  - response_time    : latency must be less than threshold (ms)
  - text_contains    : response body must contain a substring
  - json_path_equals : value at a JSON dot-path must equal expected
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("rhinometric.assertion_evaluator")

# Regex for validating JSON dot-path:  $.field.nested.array[0].value
_JSON_PATH_RE = re.compile(
    r"^\$(\.[a-zA-Z_][a-zA-Z0-9_]*(\[\d+\])?)+$"
)


# ---------------------------------------------------------------------------
# JSON path extractor (simple dot-notation, no jsonpath-ng)
# ---------------------------------------------------------------------------

def _extract_json_path(body: str, path: str) -> Any:
    """
    Extract a value from a JSON string using simple dot-notation.

    Supported syntax:  $.field.nested.items[0].name
    Raises ValueError / KeyError / TypeError / IndexError on failure.
    """
    if not _JSON_PATH_RE.match(path):
        raise ValueError(f"Invalid JSON path syntax: {path}")

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Response body is not valid JSON: {exc}")

    tokens = path[2:].split(".")  # strip leading "$."
    current = data

    for token in tokens:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]$", token)
        if m:
            field, idx = m.group(1), int(m.group(2))
            if not isinstance(current, dict):
                raise TypeError(
                    f"Expected object for key '{field}', "
                    f"got {type(current).__name__}"
                )
            if field not in current:
                raise KeyError(f"Key '{field}' not found")
            current = current[field]
            if not isinstance(current, list):
                raise TypeError(
                    f"Expected array for [{idx}], "
                    f"got {type(current).__name__}"
                )
            if idx >= len(current):
                raise IndexError(
                    f"Index [{idx}] out of range (length={len(current)})"
                )
            current = current[idx]
        else:
            if not isinstance(current, dict):
                raise TypeError(
                    f"Expected object for key '{token}', "
                    f"got {type(current).__name__}"
                )
            if token not in current:
                raise KeyError(f"Key '{token}' not found")
            current = current[token]

    return current


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def needs_body_capture(assertions: list) -> bool:
    """Return True if any assertion requires the HTTP response body."""
    return any(
        a.assertion_type in ("text_contains", "json_path_equals")
        for a in assertions
    )


def evaluate_assertions(
    assertions: list,
    check_result: dict,
    response_body: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluate assertion rules against a check result.

    Parameters
    ----------
    assertions : list[ServiceAssertion]
        Enabled assertions for the service, sorted by ``order``.
    check_result : dict
        Connector result with keys: status, status_code, response_time_ms, …
    response_body : str | None
        Raw HTTP response body (present only when capture_body was True).

    Returns
    -------
    list[dict]
        One entry per assertion::

            {
                "assertion_id": UUID,
                "assertion_name": str,
                "assertion_type": str,
                "passed": bool,
                "expected_value": str,
                "actual_value": str | None,
                "error_message": str | None,
            }
    """
    return [_evaluate_one(a, check_result, response_body) for a in assertions]


# ---------------------------------------------------------------------------
# Internal per-type evaluators
# ---------------------------------------------------------------------------

def _evaluate_one(assertion, check_result: dict, response_body: Optional[str]) -> dict:
    a_type   = assertion.assertion_type
    operator = assertion.operator
    expected = assertion.expected_value

    base: Dict[str, Any] = {
        "assertion_id":   assertion.id,
        "assertion_name": assertion.name or f"{a_type}_{operator}",
        "assertion_type": a_type,
        "expected_value": expected,
        "actual_value":   None,
        "passed":         False,
        "error_message":  None,
    }

    try:
        if a_type == "status_code":
            return _eval_status_code(base, check_result, operator, expected)
        if a_type == "response_time":
            return _eval_response_time(base, check_result, operator, expected)
        if a_type == "text_contains":
            return _eval_text_contains(base, response_body, operator, expected)
        if a_type == "json_path_equals":
            return _eval_json_path(base, assertion, response_body, operator, expected)
        base["error_message"] = f"Unknown assertion type: {a_type}"
        return base
    except Exception as exc:  # noqa: BLE001
        base["error_message"] = str(exc)[:500]
        return base


def _eval_status_code(base, check_result, operator, expected):
    actual = check_result.get("status_code")
    base["actual_value"] = str(actual) if actual is not None else None

    if actual is None:
        base["error_message"] = "No status_code in result (non-HTTP or connection failure)"
        return base
    try:
        expected_int = int(expected)
    except (ValueError, TypeError):
        base["error_message"] = f"Invalid expected status code: {expected}"
        return base

    if operator == "equals":
        base["passed"] = actual == expected_int
    elif operator == "not_equals":
        base["passed"] = actual != expected_int
    else:
        base["error_message"] = f"Unsupported operator: {operator}"
    return base


def _eval_response_time(base, check_result, operator, expected):
    actual = check_result.get("response_time_ms")
    base["actual_value"] = str(round(actual, 2)) if actual is not None else None

    if actual is None:
        base["error_message"] = "No response_time_ms in result"
        return base
    try:
        threshold = float(expected)
    except (ValueError, TypeError):
        base["error_message"] = f"Invalid expected response time: {expected}"
        return base

    if operator == "less_than":
        base["passed"] = actual < threshold
    elif operator == "greater_than":
        base["passed"] = actual > threshold
    else:
        base["error_message"] = f"Unsupported operator: {operator}"
    return base


def _eval_text_contains(base, response_body, operator, expected):
    if response_body is None:
        base["error_message"] = "Response body not captured"
        return base
    base["actual_value"] = response_body[:200]

    if operator == "contains":
        base["passed"] = expected in response_body
    elif operator == "not_contains":
        base["passed"] = expected not in response_body
    else:
        base["error_message"] = f"Unsupported operator: {operator}"
    return base


def _eval_json_path(base, assertion, response_body, operator, expected):
    jp = assertion.json_path
    if not jp:
        base["error_message"] = "json_path is required for json_path_equals"
        return base
    if response_body is None:
        base["error_message"] = "Response body not captured"
        return base

    try:
        actual = _extract_json_path(response_body, jp)
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        base["error_message"] = f"JSON path extraction failed: {exc}"
        return base

    base["actual_value"] = str(actual) if actual is not None else None

    if operator == "equals":
        base["passed"] = str(actual) == expected
    elif operator == "not_equals":
        base["passed"] = str(actual) != expected
    else:
        base["error_message"] = f"Unsupported operator: {operator}"
    return base
