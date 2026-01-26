#!/bin/bash
# Wrapper script to run the translation with the virtual environment
cd "$(dirname "$0")/.."
scripts/.venv/bin/python3 scripts/translate.py "$@"