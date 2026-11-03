#!/usr/bin/env bash
# SlidePDF Studio - Linux/macOS Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check virtual environment in project dir
if [ -d "$SCRIPT_DIR/.venv" ]; then
    PYTHON_EXEC="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_EXEC="python3"
else
    echo "Error: Python 3 is required to run SlidePDF Studio."
    exit 1
fi

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Run Desktop GUI or forward CLI arguments
if [ $# -eq 0 ]; then
    exec "$PYTHON_EXEC" -m slidepdf.app
else
    exec "$PYTHON_EXEC" -m slidepdf.cli "$@"
fi
