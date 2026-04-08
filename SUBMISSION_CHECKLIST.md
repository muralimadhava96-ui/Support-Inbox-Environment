# Submission Checklist

1. Run local verification:
   - `./verify_submission.sh`
2. Confirm OpenEnv validation:
   - `python3 -m openenv.cli.__main__ validate .`
3. Ensure required files exist:
   - `app.py`, `env.py`, `models.py`, `tasks.py`, `graders.py`
   - `openenv.yaml`, `requirements.txt`, `requirements-inference.txt`
   - `Dockerfile`, `inference.py`, `README.md`
4. Package submission:
   - `./create_submission_zip.sh`
5. If deploying to HF Space, follow:
   - `HF_SPACE_CHECKLIST.md`
