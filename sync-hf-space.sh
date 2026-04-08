#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is required."
  echo "Example:"
  echo "  export HF_TOKEN=hf_xxx"
  echo "  ./sync-hf-space.sh"
  exit 1
fi

SPACE_ID="${HF_SPACE_ID:-Madhava96/support-inbox-env}"
SOURCE_BRANCH="${SOURCE_BRANCH:-main}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"

echo "Syncing branch '${SOURCE_BRANCH}' to Space '${SPACE_ID}' (${TARGET_BRANCH})"
git push "https://hf:${HF_TOKEN}@huggingface.co/spaces/${SPACE_ID}" "${SOURCE_BRANCH}:${TARGET_BRANCH}"
echo "Done. Hugging Face Space rebuild should start automatically."
