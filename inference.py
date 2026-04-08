"""Inference runner for Support Inbox Environment."""

import argparse
import asyncio
import os

try:
    import httpx
except Exception:  # pragma: no cover - dependency may be intentionally absent in env-only runtimes
    httpx = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - dependency may be intentionally absent in env-only runtimes
    OpenAI = None


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
TEMPERATURE = 0.2

LLM_CLIENT = OpenAI(api_key=API_KEY, base_url=API_BASE_URL) if (API_KEY and OpenAI is not None) else None

POLICY_KEYWORDS = {
    "ban",
    "banned",
    "suspended",
    "restricted",
    "appeal",
    "account",
    "trust",
}
BILLING_KEYWORDS = {
    "charged",
    "charge",
    "billing",
    "invoice",
    "payment",
    "double",
}
FAQ_KEYWORDS = {
    "policy",
    "return",
    "shipping",
    "hours",
    "price",
}

SYSTEM_PROMPT = (
    "You are a customer support assistant. Write one concise, empathetic response "
    "based on the provided ticket and KB. Return plain text only."
)


def _sanitize_error(exc: Exception) -> str:
    return str(exc).replace("\n", " ").strip() or "unknown_error"


def _safe_reward(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _keyword_classify(message: str) -> str:
    lowered = message.lower()

    if any(keyword in lowered for keyword in POLICY_KEYWORDS):
        return "policy"

    if any(keyword in lowered for keyword in BILLING_KEYWORDS):
        return "billing"

    if any(keyword in lowered for keyword in FAQ_KEYWORDS):
        return "faq"

    return "faq"


def _parse_history_actions(history: list[str]) -> list[str]:
    actions: list[str] = []
    for row in history:
        if "]" not in row:
            continue
        suffix = row.split("]", 1)[1].strip()
        action_name = suffix.split(":", 1)[0].strip()
        actions.append(action_name)
    return actions


def _history_classification(history: list[str]) -> str | None:
    for row in reversed(history):
        if "classify:" not in row:
            continue
        value = row.split("classify:", 1)[1].strip().lower()
        if value in {"faq", "billing", "policy"}:
            return value
    return None


def _fallback_response(observation: dict) -> str:
    kb = observation.get("knowledge_base", [])
    first_kb = kb[0] if kb else "Please review our support policy page for next steps."
    return (
        "Thank you for reaching out. Based on our policy, "
        f"{first_kb} If you share any additional details, we can help you right away."
    )


def _llm_response(observation: dict) -> str:
    if LLM_CLIENT is None:
        return _fallback_response(observation)

    kb_text = "\n".join(f"- {line}" for line in observation.get("knowledge_base", []))
    user_prompt = (
        f"Customer message:\n{observation.get('customer_message', '')}\n\n"
        f"Knowledge base:\n{kb_text}"
    )

    try:
        response = LLM_CLIENT.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=180,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        return text if text else _fallback_response(observation)
    except Exception:
        return _fallback_response(observation)


def _decide_next_action(observation: dict, cache: dict[str, str]) -> dict:
    history = observation.get("history", [])
    actions = _parse_history_actions(history)

    if "classify" not in actions:
        ticket_type = _keyword_classify(observation.get("customer_message", ""))
        cache["ticket_type"] = ticket_type
        return {"action_type": "classify", "content": ticket_type}

    if "search_kb" not in actions:
        return {"action_type": "search_kb", "content": None}

    if "respond" not in actions:
        return {"action_type": "respond", "content": _llm_response(observation)}

    ticket_type = cache.get("ticket_type") or _history_classification(history) or "faq"
    if ticket_type == "policy":
        return {"action_type": "escalate", "content": None}

    return {"action_type": "resolve", "content": None}


async def _run_local(task: str) -> None:
    from env import SupportEnv
    from models import Action

    rewards: list[float] = []
    cache: dict[str, str] = {}
    success = False
    env = None
    result = None

    print(f"[START] task={task} env=local model={MODEL_NAME}")

    try:
        env = await SupportEnv.create(task)
        result = await env.reset()
        step = 0

        while not result.done:
            action_dict = _decide_next_action(result.observation.model_dump(), cache)
            action_name = action_dict["action_type"]
            step += 1

            try:
                result = await env.step(Action(**action_dict))
                reward = _safe_reward(result.reward)
                done = bool(result.done)
                rewards.append(reward)
                print(
                    f"[STEP] step={step} action={action_name} "
                    f"reward={reward:.2f} done={str(done).lower()} error=null"
                )
            except Exception as exc:
                rewards.append(0.0)
                print(
                    f"[STEP] step={step} action={action_name} "
                    f"reward=0.00 done=false error={_sanitize_error(exc)}"
                )
                break

            if step > 20:
                break

        if env is not None and result is not None:
            state = env.state()
            success = bool(result.done and state.get("resolved_correctly"))

    except Exception as exc:
        print(f"[STEP] step=0 action=null reward=0.00 done=false error={_sanitize_error(exc)}")

    finally:
        if env is not None:
            try:
                await env.close()
            except Exception:
                pass

        reward_csv = ",".join(f"{value:.2f}" for value in rewards)
        print(f"[END] success={str(success).lower()} steps={len(rewards)} rewards={reward_csv}")


async def _run_http(task: str) -> None:
    rewards: list[float] = []
    cache: dict[str, str] = {}
    success = False

    print(f"[START] task={task} env={ENV_BASE_URL} model={MODEL_NAME}")

    try:
        if httpx is None:
            raise RuntimeError("httpx_not_installed")

        async with httpx.AsyncClient(base_url=ENV_BASE_URL, timeout=30.0) as client:
            reset_response = await client.post("/reset", params={"task": task})
            reset_response.raise_for_status()
            result = reset_response.json()
            step = 0

            while not result.get("done", False):
                action_dict = _decide_next_action(result["observation"], cache)
                action_name = action_dict["action_type"]
                step += 1

                try:
                    step_response = await client.post("/step", json=action_dict)
                    step_response.raise_for_status()
                    result = step_response.json()
                    reward = _safe_reward(result.get("reward", 0.0))
                    done = bool(result.get("done", False))
                    rewards.append(reward)
                    print(
                        f"[STEP] step={step} action={action_name} "
                        f"reward={reward:.2f} done={str(done).lower()} error=null"
                    )
                except Exception as exc:
                    rewards.append(0.0)
                    print(
                        f"[STEP] step={step} action={action_name} "
                        f"reward=0.00 done=false error={_sanitize_error(exc)}"
                    )
                    break

                if step > 20:
                    break

            success = bool(result.get("done", False))
            if success:
                try:
                    state_resp = await client.get("/state")
                    state_resp.raise_for_status()
                    state = state_resp.json()
                    success = bool(state.get("resolved_correctly"))
                except Exception:
                    success = False

    except Exception as exc:
        print(f"[STEP] step=0 action=null reward=0.00 done=false error={_sanitize_error(exc)}")

    finally:
        reward_csv = ",".join(f"{value:.2f}" for value in rewards)
        print(f"[END] success={str(success).lower()} steps={len(rewards)} rewards={reward_csv}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference against support-inbox-env")
    parser.add_argument("--task", default=None, help="Task name (default: run all)")
    parser.add_argument("--mode", default="local", choices=["local", "http"])
    args = parser.parse_args()

    from tasks import TASKS

    tasks = [args.task] if args.task else list(TASKS.keys())
    runner = _run_http if args.mode == "http" else _run_local

    for task in tasks:
        await runner(task)


if __name__ == "__main__":
    asyncio.run(main())
