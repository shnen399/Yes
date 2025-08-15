#!/usr/bin/env bash
set -eux

# Ensure playwright package exists
python -m pip install --no-cache-dir playwright

# Run setup via Python to avoid any text translations by the browser
python - <<'PY'
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "playwright", "install-deps"])
subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
PY
