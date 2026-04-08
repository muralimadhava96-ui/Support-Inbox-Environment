import asyncio

from env import SupportEnv
from models import Action


def test_optimal_easy_faq_reaches_one():
    async def run():
        env = await SupportEnv.create("easy_faq")
        result = await env.reset()
        total = 0.0

        plan = [
            Action(action_type="classify", content="faq"),
            Action(action_type="search_kb", content=None),
            Action(
                action_type="respond",
                content=(
                    "Thanks for reaching out. Refunds are accepted within 30 days "
                    "with proof of purchase."
                ),
            ),
            Action(action_type="resolve", content=None),
        ]

        for action in plan:
            result = await env.step(action)
            total += result.reward
            if result.done:
                break

        assert result.done is True
        assert round(total, 4) == 1.0

    asyncio.run(run())


def test_reward_floor_is_enforced():
    async def run():
        env = await SupportEnv.create("easy_faq")
        result = await env.reset()
        total = 0.0

        for _ in range(10):
            if result.done:
                break
            result = await env.step(Action(action_type="respond", content=""))
            total += result.reward

        assert result.done is True
        assert round(total, 4) == -1.0

    asyncio.run(run())


def test_policy_ticket_wrong_terminal_action_penalized():
    async def run():
        env = await SupportEnv.create("hard_escalation")
        _ = await env.reset()
        result = await env.step(Action(action_type="resolve", content=None))
        assert result.done is True
        assert round(result.reward, 4) == -0.15

    asyncio.run(run())
