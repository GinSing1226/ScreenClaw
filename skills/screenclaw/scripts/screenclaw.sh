#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/screenclaw.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/screenclaw.py" "$@"
fi

echo "Script Error: python is required for screenclaw.sh fallback" >&2
exit 1
