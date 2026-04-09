"""Deterministic graders for Support Inbox Environment."""

import math
from typing import Any


SCORE_MIN = 0.01
SCORE_MAX = 0.99


def _normalize_inputs(*args: Any, **kwargs: Any) -> tuple[str | None, dict[str, Any]]:
    """Accept common grader signatures used by validators.

    Supported forms:
    - grade(state)
    - grade(task_id, state)
    - grade(state=..., task_id=...)
    - grade()
    """
    task_id = kwargs.get("task_id")
    state = kwargs.get("state")

    if len(args) == 1:
        if isinstance(args[0], dict):
            state = args[0]
        elif isinstance(args[0], str):
            task_id = args[0]
    elif len(args) >= 2:
        if isinstance(args[0], str):
            task_id = args[0]
        if isinstance(args[1], dict):
            state = args[1]

    if not isinstance(state, dict):
        state = {}
    return task_id, state


def _clamp_score(score: float) -> float:
    """Map canonical scores into the strict open interval (0, 1)."""
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return SCORE_MIN

    if not math.isfinite(numeric):
        return SCORE_MIN

    bounded = max(SCORE_MIN, min(numeric, SCORE_MAX))
    if bounded <= 0.0:
        return SCORE_MIN
    if bounded >= 1.0:
        return SCORE_MAX
    return round(bounded, 6)


def grade(*args: Any, **kwargs: Any) -> float:
    """Canonical score strictly between 0 and 1."""
    return grade_with_breakdown(*args, **kwargs)["score"]


def grade_with_breakdown(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Score plus criterion-level breakdown."""
    task_id, state = _normalize_inputs(*args, **kwargs)
    criteria = {
        "classification": bool(state.get("classified_correctly")),
        "kb_usage": bool(state.get("used_kb")),
        "response": bool(state.get("responded")),
        "resolution": bool(state.get("resolved_correctly")),
    }
    raw_score = (
        (0.30 if criteria["classification"] else 0.0)
        + (0.20 if criteria["kb_usage"] else 0.0)
        + (0.20 if criteria["response"] else 0.0)
        + (0.30 if criteria["resolution"] else 0.0)
    )
    score = _clamp_score(raw_score)
    breakdown = {name: ("pass" if passed else "fail") for name, passed in criteria.items()}
    payload = {"score": score, "total": score, "breakdown": breakdown}
    if task_id is not None:
        payload["task_id"] = task_id
    return payload


def grade_easy_faq(state: dict[str, Any]) -> float:
    return grade("easy_faq", state)


def grade_medium_billing(state: dict[str, Any]) -> float:
    return grade("medium_billing", state)


def grade_hard_escalation(state: dict[str, Any]) -> float:
    return grade("hard_escalation", state)


GRADERS = {
    "easy_faq": grade_easy_faq,
    "medium_billing": grade_medium_billing,
    "hard_escalation": grade_hard_escalation,
    # Compatibility aliases commonly used by challenge templates:
    "task_1": grade_easy_faq,
    "task_2": grade_medium_billing,
    "task_3": grade_hard_escalation,
    "task_1_basic_triage": grade_easy_faq,
    "task_2_reply_and_escalate": grade_medium_billing,
    "task_3_full_workflow": grade_hard_escalation,
}
