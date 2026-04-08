"""Deterministic graders for Support Inbox Environment."""

from typing import Any


SCORE_MIN_OPEN = 0.001
SCORE_MAX_OPEN = 0.999


def _clamp_score(score: float) -> float:
    """Ensure score is strictly between (0, 1)"""
    return max(0.01, min(0.99, float(score)))


def grade_with_breakdown(state: dict) -> dict:
    """
    Compute reward score with breakdown.
    Ensures final score is strictly within (0, 1).
    """

    classified = int(state.get("classified_correctly", False))
    used_kb = int(state.get("used_kb", False))
    responded = int(state.get("responded", False))
    resolved = int(state.get("resolved_correctly", False))

    # weighted scoring
    score = (
        0.3 * classified +
        0.2 * used_kb +
        0.25 * responded +
        0.25 * resolved
    )

    # clamp to avoid 0.0 or 1.0
    score = _clamp_score(score)

    return {
        "score": score,
        "breakdown": {
            "classified": 0.3 * classified,
            "used_kb": 0.2 * used_kb,
            "responded": 0.25 * responded,
            "resolved": 0.25 * resolved,
        }
    }
