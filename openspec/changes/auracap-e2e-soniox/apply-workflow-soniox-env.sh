#!/usr/bin/env bash
# Task 3.2 helper: adds the Soniox env block to both GitHub workflows.
# (The worker lane could not edit .github/workflows directly — CI kill-switch.)
# Idempotent: skips files that already contain SONIOX_API_KEY.
set -euo pipefail
cd "$(dirname "$0")/../../.."

python3 - <<'EOF'
from pathlib import Path

BLOCK = """
      SONIOX_API_KEY: ${{ secrets.SONIOX_API_KEY }}
      SONIOX_BASE_URL: ${{ vars.SONIOX_BASE_URL || 'https://api.soniox.com' }}
      SONIOX_MODEL: ${{ vars.AURACAP_SONIOX_MODEL || 'stt-async-v5' }}
"""

ANCHOR = "MISTRAL_ASR_MODEL: ${{ vars.MISTRAL_ASR_MODEL || 'voxtral-mini-latest' }}\n"

for wf in (".github/workflows/ingest_dispatch.yml", ".github/workflows/scheduler_tick.yml"):
    p = Path(wf)
    text = p.read_text(encoding="utf-8")
    if "SONIOX_API_KEY" in text:
        print(f"skip (already patched): {wf}")
        continue
    idx = text.index(ANCHOR) + len(ANCHOR)
    p.write_text(text[:idx] + BLOCK + text[idx:], encoding="utf-8")
    print(f"patched: {wf}")
EOF
