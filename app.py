"""FastAPI app for Support Inbox Environment."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from env import SupportEnv
from support_inbox_env.graders import grade_with_breakdown
from models import Action, Observation
from tasks import TASKS


env_registry: dict[str, SupportEnv] = {}
ENV_NAME = "support-inbox-env"
ENV_DESCRIPTION = "Customer support ticket-resolution environment."
ENV_VERSION = "1.0.0"
_UI_TEMPLATE = Path(__file__).parent / "templates" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for env in env_registry.values():
        await env.close()
    env_registry.clear()


app = FastAPI(
    title="Support Inbox OpenEnv",
    description=ENV_DESCRIPTION,
    version=ENV_VERSION,
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
        "name": ENV_NAME,
        "version": ENV_VERSION,
        "tasks": list(TASKS.keys()),
        "endpoints": ["/reset", "/step", "/state"],
    }


@app.get("/ui", response_class=HTMLResponse)
async def ui():
    return _UI_TEMPLATE.read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"status": "healthy", "name": ENV_NAME, "version": ENV_VERSION}


@app.get("/metadata")
async def metadata():
    return {
        "name": ENV_NAME,
        "description": ENV_DESCRIPTION,
        "version": ENV_VERSION,
        "tasks": list(TASKS.keys()),
        "reward": {"min": -1.0, "max": 0.999, "shaped": True},
        "endpoints": {"reset": "POST /reset", "step": "POST /step", "state": "GET /state"},
    }


@app.get("/schema")
async def schema():
    state_schema = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "customer_message": {"type": "string"},
            "history": {"type": "array", "items": {"type": "string"}},
            "knowledge_base": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "enum": ["open", "resolved", "escalated"]},
            "task_type": {"type": "string"},
            "expected_resolution": {"type": "string", "enum": ["resolve", "escalate"]},
            "classified_correctly": {"type": "boolean"},
            "used_kb": {"type": "boolean"},
            "responded": {"type": "boolean"},
            "response_bonus_awarded": {"type": "boolean"},
            "resolved_correctly": {"type": "boolean"},
            "has_classified": {"type": "boolean"},
        },
        "required": [
            "ticket_id",
            "customer_message",
            "history",
            "knowledge_base",
            "status",
            "task_type",
            "expected_resolution",
            "classified_correctly",
            "used_kb",
            "responded",
            "response_bonus_awarded",
            "resolved_correctly",
            "has_classified",
        ],
    }
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": state_schema,
    }


@app.post("/mcp")
async def mcp(payload: dict[str, Any]):
    method = payload.get("method")
    request_id = payload.get("id")

    if method == "initialize":
        result: dict[str, Any] = {
            "capabilities": {},
            "serverInfo": {"name": ENV_NAME, "version": ENV_VERSION},
        }
    elif method == "tools/list":
        result = {"tools": []}
    else:
        result = {"ok": True}

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


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
        return grade_with_breakdown({})

    return grade_with_breakdown(env.state())
