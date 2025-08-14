#!/usr/bin/env bash
set -e
echo "===> Installing Python deps"
pip install -r requirements.txt
echo "===> Installing Playwright browsers (chromium)"
python -m playwright install chromium
# 可選：顯示一下安裝到哪
python - <<'PY'
import os, json, pathlib
base = pathlib.Path.home()/".cache"/"ms-playwright"
paths = list(base.glob("*/chrome-*/*/chrome")) + list(base.glob("*/chrome-linux/chrome"))
print("Playwright cache base:", base)
print("Chromium found:", [str(p) for p in paths])
PY
