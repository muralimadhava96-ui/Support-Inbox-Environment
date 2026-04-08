#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: ./validate-submission.sh <openenv-base-url>"
  echo "Example: ./validate-submission.sh https://your-space.hf.space"
  exit 1
fi

BASE_URL="${1%/}"

echo "[1/3] Waking target environment via /reset"
curl -sS -X POST "$BASE_URL/reset" > /tmp/openenv_reset_response.json
cat /tmp/openenv_reset_response.json

echo "[2/3] Running OpenEnv runtime validation"
python3 -m openenv.cli.__main__ validate --url "$BASE_URL" --timeout 20

echo "[3/3] Re-checking /state availability"
curl -sS "$BASE_URL/state" || true

echo "Live submission validation finished."
