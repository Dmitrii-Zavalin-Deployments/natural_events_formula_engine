#!/bin/bash
set -euo pipefail

echo "📦 Installing solver dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt

echo "✅ Environment setup completed successfully."
