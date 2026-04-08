# Repository Structure (Submission Ready)

This repository is organized for OpenEnv validation, Hugging Face Docker deployment, and repeatable submission packaging.

## Required Core Files

```text
app.py
env.py
models.py
tasks.py
graders.py
openenv.yaml
requirements.txt
requirements-inference.txt
Dockerfile
inference.py
README.md
```

## Packaging and Validation Files

```text
pyproject.toml
uv.lock
verify_submission.sh
create_submission_zip.sh
SUBMISSION_CHECKLIST.md
HF_SPACE_CHECKLIST.md
pytest.ini
```

## Server Entrypoint (OpenEnv Multi-Mode)

```text
server/
├── __init__.py
└── app.py
```

## Test and CI

```text
tests/
├── test_api.py
└── test_env.py

.github/workflows/validate.yml
.github/ISSUE_TEMPLATE/*
.github/pull_request_template.md
```

## Submission Artifact

Run:

```bash
./create_submission_zip.sh
```

This produces:

```text
submission-support-inbox-env-<timestamp>.zip
```
