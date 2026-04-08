#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Running OpenEnv validation"
python3 -m openenv.cli.__main__ validate .

echo "[2/5] Running API smoke tests"
python3 - <<'PY'
import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)
assert client.get('/').status_code == 200
assert client.get('/tasks').status_code == 200
r = client.post('/reset', params={'task': 'easy_faq', 'session_id': 'ci'})
assert r.status_code == 200
s = client.post('/step', params={'session_id': 'ci'}, json={'action_type': 'classify', 'content': 'faq'})
assert s.status_code == 200
st = client.get('/state', params={'session_id': 'ci'})
assert st.status_code == 200
print('api_smoke=ok')
PY

echo "[3/5] Running pytest suite"
python3 -m pytest

echo "[4/5] Running inference local-mode smoke"
python3 inference.py --task easy_faq --mode local > /tmp/support_inbox_infer.log
cat /tmp/support_inbox_infer.log

python3 - <<'PY'
import re
from pathlib import Path

lines = [ln for ln in Path('/tmp/support_inbox_infer.log').read_text().splitlines() if ln.strip()]
assert lines, 'inference produced no output'

pat_start = re.compile(r'^\[START\] task=\S+ env=\S+ model=\S+$')
pat_step = re.compile(r'^\[STEP\] step=\d+ action=\S+ reward=-?\d+\.\d{2} done=(true|false) error=(null|.+)$')
pat_end = re.compile(r'^\[END\] success=(true|false) steps=\d+ rewards=.*$')

assert pat_start.match(lines[0]), f'invalid START line: {lines[0]}'
assert pat_end.match(lines[-1]), f'invalid END line: {lines[-1]}'
for ln in lines[1:-1]:
    assert pat_step.match(ln), f'invalid STEP line: {ln}'

print('inference_format=ok')
PY

echo "[5/5] Verifying reward bounds + optimal path"
python3 - <<'PY'
import asyncio
from env import SupportEnv
from models import Action

OPT = [
    Action(action_type='classify', content='faq'),
    Action(action_type='search_kb', content=None),
    Action(action_type='respond', content='Thanks for reaching out. Refunds are accepted within 30 days with proof of purchase.'),
    Action(action_type='resolve', content=None),
]

async def check_optimal():
    env = await SupportEnv.create('easy_faq')
    r = await env.reset()
    total = 0.0
    for a in OPT:
        r = await env.step(a)
        total += r.reward
        if r.done:
            break
    assert round(total, 4) == 1.0, f'expected optimal total 1.0, got {total}'

asyncio.run(check_optimal())
print('reward_optimal=ok')
PY

echo "All checks passed."
