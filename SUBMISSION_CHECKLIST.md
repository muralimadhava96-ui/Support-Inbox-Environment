# Submission Checklist

1. Use submission branch:
   - `git checkout submission/ready`
2. Run local verification:
   - `./verify_submission.sh`
3. Confirm OpenEnv validation:
   - `python3 -m openenv.cli.__main__ validate .`
4. Ensure required files exist:
   - `app.py`, `env.py`, `models.py`, `tasks.py`, `graders.py`
   - `openenv.yaml`, `requirements.txt`, `requirements-inference.txt`
   - `Dockerfile`, `inference.py`, `README.md`
5. Package submission:
   - `./create_submission_zip.sh`
6. If deploying to HF Space, follow:
   - `HF_SPACE_CHECKLIST.md`
7. Run live validator against deployed URL:
   - `./validate-submission.sh https://your-space.hf.space`
