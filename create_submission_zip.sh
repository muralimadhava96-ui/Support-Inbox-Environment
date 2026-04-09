#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="submission-support-inbox-env-${STAMP}.zip"

echo "Running verification before packaging..."
./verify_submission.sh

echo "Creating ${OUT}"
zip -r "$OUT" \
  app.py env.py models.py tasks.py graders.py grader.py \
  support_inbox_env \
  openenv.yaml requirements.txt requirements-inference.txt \
  Dockerfile inference.py README.md \
  pyproject.toml uv.lock \
  server tests pytest.ini .github \
  HF_SPACE_CHECKLIST.md SUBMISSION_CHECKLIST.md REPO_STRUCTURE.md \
  verify_submission.sh validate-submission.sh create_submission_zip.sh .env.example .gitignore \
  -x "*/__pycache__/*" "*.pyc" "*.pyo" "*.DS_Store"

echo "Created: ${OUT}"
