#!/usr/bin/env bash
set -euo pipefail

echo "=== DIAGNOSTICS: Inspect Python path and test directory structure ==="
python3 -c "import sys; print(sys.path)"
find src tests -maxdepth 2 -type f

echo "=== SMOKING-GUN SOURCE AUDIT ==="
cat -n tests/test_integration.py

echo "=== AUTOMATED REPAIRS: Inject src path setup into test_integration.py ==="
python3 - << 'PYTHON_FIX'
path = "tests/test_integration.py"
with open(path, "r") as f:
    code = f.read()

# Ensure src directory is explicitly prepended to sys.path in test_integration.py
path_injection = """import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
"""

if "sys.path.insert" not in code:
    code = path_injection + code

with open(path, "w") as f:
    f.write(code)

print("Successfully injected path fix into tests/test_integration.py")
PYTHON_FIX