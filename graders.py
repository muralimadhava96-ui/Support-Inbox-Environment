"""Deterministic graders for Support Inbox Environment."""

from typing import Any


SCORE_MIN_OPEN = 0.001
SCORE_MAX_OPEN = 0.999


def _to_open_interval(raw_score: float) -> float:
    """Map raw score to a strict open interval required by Phase-2 validator."""
    if raw_score <= 0.0:
        return SCORE_MIN_OPEN
    if raw_score >= 1.0:
        return SCORE_MAX_OPEN
    return raw_score


def grade(state: dict[str, Any]) -> float:
    """
    Canonical score in strict open interval (0.0, 1.0).

    Weights:
      +0.30 classified correctly
      +0.20 used KB
      +0.20 responded
      +0.30 terminal action was correct
    """
    score = 0.0

    if state.get("classified_correctly"):
        score += 0.30

    if state.get("used_kb"):
        score += 0.20

    if state.get("responded"):
        score += 0.20

    if state.get("resolved_correctly"):
        score += 0.30

    bounded = min(max(score, 0.0), 1.0)
    return round(_to_open_interval(bounded), 4)


def grade_with_breakdown(state: dict[str, Any]) -> dict[str, Any]:
    """Score plus criterion-level breakdown."""
    breakdown = {
        "classification": 0.30 if state.get("classified_correctly") else 0.0,
        "kb_usage": 0.20 if state.get("used_kb") else 0.0,
        "response": 0.20 if state.get("responded") else 0.0,
        "resolution": 0.30 if state.get("resolved_correctly") else 0.0,
    }
    raw_total = min(max(sum(breakdown.values()), 0.0), 1.0)
    total = round(_to_open_interval(raw_total), 4)
    return {"total": total, "breakdown": breakdown}
