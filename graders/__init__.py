"""Package-style grader exports for scaffold/validator compatibility."""

from .graders import GRADERS, grade, grade_with_breakdown

__all__ = ["grade", "grade_with_breakdown", "GRADERS"]
