"""Deterministic graders for Support Inbox Environment."""

from typing import Any


def grade(state: dict[str, Any]) -> float:
    """
    Canonical score in [0.0, 1.0].

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

    return round(min(score, 1.0), 4)


def grade_with_breakdown(state: dict[str, Any]) -> dict[str, Any]:
    """Score plus criterion-level breakdown."""
    breakdown = {
        "classification": 0.30 if state.get("classified_correctly") else 0.0,
        "kb_usage": 0.20 if state.get("used_kb") else 0.0,
        "response": 0.20 if state.get("responded") else 0.0,
        "resolution": 0.30 if state.get("resolved_correctly") else 0.0,
    }
    total = round(min(sum(breakdown.values()), 1.0), 4)
    return {"total": total, "breakdown": breakdown}
