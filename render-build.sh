#!/usr/bin/env bash
set -euxo pipefail

# 安裝 Python 依賴
pip install --no-deps -r requirements.txt

# 安裝 Playwright 瀏覽器
python -m playwright install --with-deps chromium
