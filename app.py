"""FastAPI app for Support Inbox Environment."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from env import SupportEnv
from graders import grade_with_breakdown
from models import Action
from tasks import TASKS


env_registry: dict[str, SupportEnv] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for env in env_registry.values():
        await env.close()
    env_registry.clear()


app = FastAPI(
    title="Support Inbox OpenEnv",
    description="Customer support ticket-resolution environment.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "support-inbox-env",
        "version": "1.0.0",
        "tasks": list(TASKS.keys()),
        "endpoints": ["/reset", "/step", "/state"],
    }


@app.get("/tasks")
async def list_tasks():
    return {
        name: {
            "type": task["type"],
            "description": task["description"],
            "expected_resolution": task["expected_resolution"],
        }
        for name, task in TASKS.items()
    }


@app.post("/reset")
async def reset(task: str = "easy_faq", session_id: Optional[str] = "default"):
    sid = session_id or "default"

    if task not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task '{task}'.")

    previous = env_registry.get(sid)
    if previous is not None:
        await previous.close()

    env = await SupportEnv.create(task)
    result = await env.reset()
    env_registry[sid] = env
    return result.to_dict()


@app.post("/step")
async def step(action: Action, session_id: Optional[str] = "default"):
    sid = session_id or "default"
    env = env_registry.get(sid)

    if env is None:
        raise HTTPException(status_code=400, detail="No active session. Call /reset first.")

    if env.done:
        raise HTTPException(status_code=400, detail="Episode done. Call /reset to restart.")

    result = await env.step(action)
    return result.to_dict()


@app.get("/state")
async def get_state(session_id: Optional[str] = "default"):
    sid = session_id or "default"
    env = env_registry.get(sid)

    if env is None:
        raise HTTPException(status_code=400, detail="No active session.")

    return env.state()


@app.get("/score")
async def get_score(session_id: Optional[str] = "default"):
    sid = session_id or "default"
    env = env_registry.get(sid)

    if env is None:
        raise HTTPException(status_code=400, detail="No active session.")

    return grade_with_breakdown(env.state())
