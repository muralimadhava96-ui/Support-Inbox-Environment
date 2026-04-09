"""Compatibility import path for graders."""

from support_inbox_env.graders import GRADERS, grade, grade_with_breakdown

__all__ = ["grade", "grade_with_breakdown", "GRADERS"]
