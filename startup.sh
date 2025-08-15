#!/usr/bin/env bash
set -eux

# 在執行階段安裝 Playwright 需要的瀏覽器
python -m playwright install chromium

# 啟動 FastAPI
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
