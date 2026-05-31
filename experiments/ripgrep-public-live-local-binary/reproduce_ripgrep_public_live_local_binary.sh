#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

RESULT_DIR="results/live/ripgrep-public-local-binary"
RESULT_JSON="$RESULT_DIR/live_local_binary_search_result.json"
RESULT_MD="$RESULT_DIR/live_local_binary_search_report.md"
TRACE_JSONL="$RESULT_DIR/live_local_binary_search_trace.jsonl"

"$PYTHON_BIN" tools/run_ripgrep_public_live_local_binary.py
"$PYTHON_BIN" -m json.tool "$RESULT_JSON" >/dev/null
"$PYTHON_BIN" tools/validate_ripgrep_public_live_local_binary.py \
  --result "$RESULT_JSON" \
  --report "$RESULT_MD" \
  --trace "$TRACE_JSONL"
"$PYTHON_BIN" tools/validate_traces.py "$TRACE_JSONL"

"$PYTHON_BIN" - "$RESULT_DIR" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
slash = chr(47)
patterns = (
    slash + "Users" + slash,
    slash + "private" + slash + "var" + slash + "folders" + slash,
    slash + "var" + slash + "folders" + slash,
)
for path in sorted(p for p in root.rglob("*") if p.is_file()):
    text = path.read_text(encoding="utf-8")
    if any(pattern in text for pattern in patterns):
        raise SystemExit(f"local path leakage detected in {path}")
PY

echo "ripgrep-public live local-binary reproduction passed"
