#!/usr/bin/env bash
set -e
pip install --no-cache-dir -r requirements.txt
python -m playwright install --with-deps chromium
echo "✅ Build steps done."
