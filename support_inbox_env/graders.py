"""Deterministic graders for Support Inbox Environment."""

import math
from typing import Any


SCORE_MIN = 0.001
SCORE_MAX = 0.999


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
    breakdown = {
        "classification": 0.30 if state.get("classified_correctly") else 0.0,
        "kb_usage": 0.20 if state.get("used_kb") else 0.0,
        "response": 0.20 if state.get("responded") else 0.0,
        "resolution": 0.30 if state.get("resolved_correctly") else 0.0,
    }
    score = _clamp_score(sum(breakdown.values()))
    return {"score": score, "total": score, "breakdown": breakdown}
