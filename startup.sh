#!/usr/bin/env bash
set -eux

# 執行時安裝 chromium 瀏覽器
python -m playwright install chromium

# 啟動 FastAPI
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
