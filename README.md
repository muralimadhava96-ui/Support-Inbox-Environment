# Support Inbox Environment

[![OpenEnv Validate](https://img.shields.io/badge/OpenEnv-validate%20passing-brightgreen)](https://github.com/meta-pytorch/OpenEnv)
[![CI Template](https://github.com/muralimadhava96-ui/Support-Inbox-Environment/actions/workflows/validate.yml/badge.svg)](https://github.com/muralimadhava96-ui/Support-Inbox-Environment/actions/workflows/validate.yml)

Support Inbox Environment is a production-ready OpenEnv environment that simulates a real customer support workflow. Agents must classify tickets, search the knowledge base, respond to users, and choose the correct terminal action (`resolve` or `escalate`).

Environment runtime does not require LLM APIs. Inference script does.

## Project Structure

```text
support-inbox-env/
├── app.py
├── env.py
├── models.py
├── tasks.py
├── graders.py
├── openenv.yaml
├── requirements.txt
├── requirements-inference.txt
├── Dockerfile
├── inference.py
├── README.md
├── pyproject.toml
├── uv.lock
└── server/
    ├── __init__.py
    └── app.py
```

## Tasks

- `easy_faq`: simple refund-policy question, expected terminal action `resolve`
- `medium_billing`: double-charge billing dispute, expected terminal action `resolve`
- `hard_escalation`: account-ban policy case, expected terminal action `escalate`

All tasks are deterministic and support canonical score `1.0`.

## Observation Schema

```json
{
  "ticket_id": "string",
  "customer_message": "string",
  "history": ["string"],
  "knowledge_base": ["string"],
  "status": "open | resolved | escalated"
}
```

## Action Space

```json
{ "action_type": "classify",  "content": "faq | billing | policy" }
{ "action_type": "search_kb", "content": null }
{ "action_type": "respond",   "content": "<reply text>" }
{ "action_type": "escalate",  "content": null }
{ "action_type": "resolve",   "content": null }
```

## Reward Design

Dense reward components:

- `+0.30` correct classification
- `+0.20` correct KB usage
- `+0.20` valid response
- `+0.05` response length bonus (`len(content) > 20`)
- `+0.30` correct terminal action

Penalties:

- `-0.15` incorrect action
- `-0.05` redundant action

Bounds and optimality:

- cumulative reward is clamped to `[-1.0, 1.0]` every step
- manifest bounds match runtime bounds
- optimal trajectory reaches exactly `1.0` cumulative reward

Canonical final score from `graders.py`:

- `0.30` classified correctly
- `0.20` used KB
- `0.20` responded
- `0.30` resolved/escalated correctly

## API Endpoints

Core OpenEnv endpoints:

- `POST /reset`
- `POST /step`
- `GET /state`

Additional utility endpoints:

- `GET /`
- `GET /tasks`
- `GET /score`

Session lifecycle: `/reset` closes any previous session instance before replacing it.

## Dependencies

Environment-only (`requirements.txt`):

- `fastapi`
- `uvicorn`
- `pydantic`

Inference-only (`requirements-inference.txt`):

- `openai`
- `httpx`

## Local Run

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

## Inference Run

```bash
pip install -r requirements.txt -r requirements-inference.txt
export OPENAI_API_KEY=sk-...   # or export HF_TOKEN=...
python inference.py --mode local
python inference.py --mode http
python inference.py --task medium_billing --mode local
```

Optional inference environment variables:

- `API_BASE_URL` (default: `https://api.openai.com/v1`)
- `MODEL_NAME` (default: `gpt-4o-mini`)
- `ENV_BASE_URL` (default: `http://localhost:7860`)

## Strict Inference Logs

`inference.py` emits:

```text
[START] task=<task> env=<env> model=<model>
[STEP] step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> rewards=<r1,r2,...>
```

Guarantees:

- reward uses 2-decimal formatting
- booleans are lowercase
- no extra fields
- `END` is always emitted

## Hugging Face Spaces (Docker)

1. Create a new Hugging Face Space with Docker SDK.
2. Push this repository.
3. Space runs `uvicorn app:app --host 0.0.0.0 --port 7860`.
4. For remote agent execution:

```bash
export ENV_BASE_URL=https://<your-space>.hf.space
python inference.py --mode http
```

## OpenEnv Validation

```bash
openenv validate .
```

This repository is structured to satisfy OpenEnv multi-mode validation requirements.


## Testing

- Run quick project validation: `./verify_submission.sh`
- Run pytest only: `python3 -m pytest`
- Create release zip: `./create_submission_zip.sh`


## Live Validator

- Validate deployed Space/runtime: `./validate-submission.sh https://your-space.hf.space`

## Automation

- Local one-command verification: `./verify_submission.sh`
- CI workflow: `.github/workflows/validate.yml`
- Deployment checklist: `HF_SPACE_CHECKLIST.md`
