#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/recording_windows.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/recording_windows.py" "$@"
fi

echo "Script Error: python is required for recording_windows.sh. On Windows, use recording_windows.ps1." >&2
exit 1
