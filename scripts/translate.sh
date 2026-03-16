#!/bin/bash
cd "$(dirname "$0")/.."

if [ -x "scripts/.venv/bin/python3" ]; then
  scripts/.venv/bin/python3 scripts/translate.py "$@"
else
  python3 scripts/translate.py "$@"
fi
