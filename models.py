from typing import Literal, Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Observation returned by reset() and step()."""

    ticket_id: str
    customer_message: str
    history: list[str]
    knowledge_base: list[str]
    status: Literal["open", "resolved", "escalated"]


class Action(BaseModel):
    """Action submitted by the agent."""

    action_type: Literal["classify", "search_kb", "respond", "escalate", "resolve"]
    content: Optional[str] = None


class Reward(BaseModel):
    """Structured reward metadata."""

    value: float = Field(..., ge=-1.0, le=1.0)
    reason: str
