# Hugging Face Space Deployment Checklist

## Preflight (Local)

1. Ensure dependencies are installed:
   - `pip install -r requirements.txt -r requirements-inference.txt`
   - `pip install openenv-core`
2. Run verification:
   - `./verify_submission.sh`
3. Confirm OpenEnv validation:
   - `python3 -m openenv.cli.__main__ validate .`

## Create the Space

1. In Hugging Face, create a new Space.
2. Select SDK: **Docker**.
3. Choose visibility and hardware.
4. Use repository name (example): `support-inbox-env`.

## Push Repository

1. Push the entire project to the Space remote (including `Dockerfile`, `openenv.yaml`, `pyproject.toml`, `uv.lock`):
   - `export HF_TOKEN=hf_xxx`
   - `export HF_SPACE_ID=Madhava96/support-inbox-env`
   - `./sync-hf-space.sh`
2. Confirm build logs show container start with `uvicorn app:app` on port `7860`.

## Runtime Checks (After Deploy)

1. Hit root endpoint:
   - `GET https://<space>.hf.space/`
2. Reset a task:
   - `POST https://<space>.hf.space/reset?task=easy_faq`
3. Verify state endpoint:
   - `GET https://<space>.hf.space/state`

## Optional Inference Against Space

1. Set environment URL locally:
   - `export ENV_BASE_URL=https://<space>.hf.space`
2. Run inference:
   - `python inference.py --mode http --task medium_billing`

## Secrets

- Environment server itself requires no LLM secret.
- If running `inference.py` with live OpenAI calls, set one of:
  - `OPENAI_API_KEY`
  - `HF_TOKEN` (fallback in script)
