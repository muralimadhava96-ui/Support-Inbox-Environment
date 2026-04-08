from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root_and_tasks_available():
    assert client.get("/").status_code == 200
    assert client.get("/tasks").status_code == 200


def test_validator_endpoints_available():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    metadata = client.get("/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["name"] == "support-inbox-env"

    schema = client.get("/schema")
    assert schema.status_code == 200
    payload = schema.json()
    assert "action" in payload
    assert "observation" in payload
    assert "state" in payload

    mcp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert mcp.status_code == 200
    assert mcp.json()["jsonrpc"] == "2.0"


def test_reset_step_state_flow():
    reset_resp = client.post("/reset", params={"task": "medium_billing", "session_id": "pytest"})
    assert reset_resp.status_code == 200

    step_resp = client.post(
        "/step",
        params={"session_id": "pytest"},
        json={"action_type": "classify", "content": "billing"},
    )
    assert step_resp.status_code == 200
    assert round(step_resp.json()["reward"], 2) == 0.30

    state_resp = client.get("/state", params={"session_id": "pytest"})
    assert state_resp.status_code == 200
    assert state_resp.json()["task_type"] == "billing"


def test_unknown_task_returns_400():
    bad_resp = client.post("/reset", params={"task": "does_not_exist"})
    assert bad_resp.status_code == 400


def test_step_after_done_returns_safe_terminal_payload():
    sid = "pytest-done-safe"
    reset_resp = client.post("/reset", params={"task": "easy_faq", "session_id": sid})
    assert reset_resp.status_code == 200

    plan = [
        {"action_type": "classify", "content": "faq"},
        {"action_type": "search_kb", "content": None},
        {
            "action_type": "respond",
            "content": (
                "Thanks for reaching out. Refunds are accepted within 30 days with proof of purchase."
            ),
        },
        {"action_type": "resolve", "content": None},
    ]

    last = None
    for action in plan:
        last = client.post("/step", params={"session_id": sid}, json=action)
        assert last.status_code == 200
    assert last is not None
    assert last.json()["done"] is True

    post_done = client.post(
        "/step",
        params={"session_id": sid},
        json={"action_type": "resolve", "content": None},
    )
    assert post_done.status_code == 200
    payload = post_done.json()
    assert payload["done"] is True
    assert payload["reward"] == 0.0
    assert payload["info"]["reason"] == "episode_done"
