#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "[BLOCKED] Project virtual environment not found: $PYTHON" >&2
  exit 2
fi
exec "$PYTHON" -X utf8 "$ROOT/start_demo.py" "$@"
