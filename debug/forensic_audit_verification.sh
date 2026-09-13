#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. DIAGNOSTICS: ENV & PIP AUDIT ==="
which python3 || true
python3 --version || true
python3 -m pip list || true
cat -n requirements.txt || true

echo "=== 2. SMOKING-GUN SOURCE AUDIT (cat -n) ==="
cat -n tests/conftest.py || true

echo "=== 3. AUTOMATED REPAIRS (Dependency Sync / Install) ==="
if [ -f requirements.txt ]; then
    python3 -m pip install -r requirements.txt || true
fi
python3 -m pip install opencv-python numpy pytest pytest-cov || true

echo "=== 4. POST-REPAIR VERIFICATION ==="
python3 -m pytest -s tests/ -vv --cov=src --cov-report=term-missing