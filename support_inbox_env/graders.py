"""Deterministic graders for Support Inbox Environment."""

import math
from typing import Any


SCORE_MIN = 0.01
SCORE_MAX = 0.99


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


def grade(state: dict[str, Any]) -> float:
    """Canonical score strictly between 0 and 1."""
    return grade_with_breakdown(state)["score"]


def grade_with_breakdown(state: dict[str, Any]) -> dict[str, Any]:
    """Score plus criterion-level breakdown."""
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
    return {"score": score, "total": score, "breakdown": breakdown}
