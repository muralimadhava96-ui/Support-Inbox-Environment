"""Core OpenEnv environment for Support Inbox."""

import uuid
from typing import Any

from support_inbox_env.graders import grade
from models import Action, Observation
from tasks import TASKS


REWARD_MIN = -1.0
REWARD_MAX = 0.999
QUALITY_THRESHOLD = 20


class StepResult:
    """Return object for reset() and step()."""

    def __init__(self, observation: Observation, reward: float, done: bool, info: dict | None = None):
        self.observation = observation
        self.reward = reward
        self.done = done
        self.info = info or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation": self.observation.model_dump(),
            "reward": self.reward,
            "done": self.done,
            "info": self.info,
        }


class SupportEnv:
    """Customer support workflow environment."""

    MAX_STEPS = 10

    def __init__(self, task_name: str):
        if task_name not in TASKS:
            raise ValueError(f"Unknown task '{task_name}'. Valid tasks: {list(TASKS.keys())}")

        self.task_name = task_name
        self.task = TASKS[task_name]
        self.done = False
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._state: dict[str, Any] = {}

    @classmethod
    async def create(cls, task: str = "easy_faq") -> "SupportEnv":
        return cls(task)

    async def reset(self) -> StepResult:
        self.done = False
        self._step_count = 0
        self._cumulative_reward = 0.0

        self._state = {
            "ticket_id": str(uuid.uuid4()),
            "customer_message": self.task["message"],
            "history": [],
            "knowledge_base": list(self.task["kb"]),
            "status": "open",
            "task_type": self.task["type"],
            "expected_resolution": self.task["expected_resolution"],
            "classified_correctly": False,
            "used_kb": False,
            "responded": False,
            "response_bonus_awarded": False,
            "resolved_correctly": False,
            "has_classified": False,
        }

        return StepResult(
            observation=self._build_observation(),
            reward=0.0,
            done=False,
            info={"task": self.task_name, "step": 0},
        )

    async def step(self, action: Action) -> StepResult:
        if not self._state:
            raise RuntimeError("Environment is not initialized. Call reset() first.")

        if self.done:
            return StepResult(
                observation=self._build_observation(),
                reward=0.0,
                done=True,
                info={"reason": "episode_done", "step": self._step_count, "status": self._state["status"]},
            )

        if self._step_count >= self.MAX_STEPS:
            self.done = True
            return StepResult(
                observation=self._build_observation(),
                reward=0.0,
                done=True,
                info={"reason": "max_steps", "step": self._step_count, "status": self._state["status"]},
            )

        try:
            action_type = action.action_type
        except Exception:
            malformed_delta = self._apply_reward_bounds(-0.1)
            return StepResult(
                observation=self._build_observation(),
                reward=round(malformed_delta, 4),
                done=False,
                info={"error": "malformed_action", "step": self._step_count, "status": self._state["status"]},
            )

        self._step_count += 1
        reward_delta = 0.0
        info: dict[str, Any] = {
            "action": action_type,
            "step": self._step_count,
            "status": self._state["status"],
        }

        if action_type == "classify":
            reward_delta, feedback = self._handle_classify(action)
            info["feedback"] = feedback

        elif action_type == "search_kb":
            reward_delta, feedback = self._handle_search_kb()
            info["feedback"] = feedback

        elif action_type == "respond":
            reward_delta, feedback = self._handle_respond(action)
            info["feedback"] = feedback

        elif action_type in {"resolve", "escalate"}:
            reward_delta, feedback = self._handle_terminal(action)
            info["feedback"] = feedback

        else:
            reward_delta = -0.15
            info["feedback"] = "Invalid action type. Incorrect action penalty applied."

        self._append_history(action)

        if self._step_count >= self.MAX_STEPS and not self.done:
            self.done = True
            info["feedback"] = "Max steps reached. Episode terminated."

        bounded_delta = self._apply_reward_bounds(reward_delta)

        info["status"] = self._state["status"]
        info["cumulative_reward"] = round(self._cumulative_reward, 4)
        info["final_score"] = grade(self._state) if self.done else None

        return StepResult(
            observation=self._build_observation(),
            reward=round(bounded_delta, 4),
            done=self.done,
            info=info,
        )

    def state(self) -> dict[str, Any]:
        snapshot = dict(self._state)
        snapshot["history"] = list(self._state.get("history", []))
        snapshot["knowledge_base"] = list(self._state.get("knowledge_base", []))
        return snapshot

    async def close(self) -> None:
        pass

    def _handle_classify(self, action: Action) -> tuple[float, str]:
        if self._state["has_classified"]:
            return -0.05, "Classification already provided. Redundant action penalty applied."

        self._state["has_classified"] = True
        predicted = (action.content or "").strip().lower()

        if predicted == self.task["type"]:
            self._state["classified_correctly"] = True
            return 0.30, "Correct classification."

        return -0.15, f"Incorrect classification '{predicted}'."

    def _handle_search_kb(self) -> tuple[float, str]:
        if self._state["used_kb"]:
            return -0.05, "Knowledge base already searched. Redundant action penalty applied."

        if not self._state["has_classified"]:
            return -0.15, "Search attempted before classification. Incorrect action penalty applied."

        self._state["used_kb"] = True
        return 0.20, "Knowledge base searched successfully."

    def _handle_respond(self, action: Action) -> tuple[float, str]:
        if self._state["responded"]:
            return -0.05, "Response already sent. Redundant action penalty applied."

        if not self._state["used_kb"]:
            return -0.15, "Respond attempted before KB search. Incorrect action penalty applied."

        text = (action.content or "").strip()
        if not text:
            return -0.15, "Empty response content. Incorrect action penalty applied."

        self._state["responded"] = True
        reward = 0.20

        if len(text) > QUALITY_THRESHOLD:
            reward += 0.05
            self._state["response_bonus_awarded"] = True

        return reward, "Customer response sent successfully."

    def _handle_terminal(self, action: Action) -> tuple[float, str]:
        expected = self.task["expected_resolution"]
        premature_resolve_penalty = 0.0

        if action.action_type == "resolve" and not self._state["responded"]:
            premature_resolve_penalty = -0.25

        if action.action_type == expected:
            self._state["resolved_correctly"] = True
            self._state["status"] = "escalated" if action.action_type == "escalate" else "resolved"
            self.done = True
            reward = 0.30 + premature_resolve_penalty
            if premature_resolve_penalty < 0:
                return reward, "Correct terminal action, but resolve occurred before response."
            return reward, "Correct terminal action. Episode complete."

        self.done = True
        return -0.15, "Incorrect terminal action. Episode complete with penalty."

    def _append_history(self, action: Action) -> None:
        entry = f"[step {self._step_count}] {action.action_type}"
        if action.content:
            entry += f": {action.content}"
        self._state["history"].append(entry)

    def _apply_reward_bounds(self, reward_delta: float) -> float:
        proposed_total = self._cumulative_reward + reward_delta

        if proposed_total > REWARD_MAX:
            bounded_delta = REWARD_MAX - self._cumulative_reward
            self._cumulative_reward = REWARD_MAX
            return bounded_delta

        if proposed_total < REWARD_MIN:
            bounded_delta = REWARD_MIN - self._cumulative_reward
            self._cumulative_reward = REWARD_MIN
            return bounded_delta

        self._cumulative_reward = proposed_total
        return reward_delta

    def _build_observation(self) -> Observation:
        return Observation(
            ticket_id=self._state["ticket_id"],
            customer_message=self._state["customer_message"],
            history=list(self._state["history"]),
            knowledge_base=list(self._state["knowledge_base"]),
            status=self._state["status"],
        )
