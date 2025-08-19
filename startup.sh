#!/usr/bin/env bash
set -euxo pipefail
# 啟動 FastAPI
uvicorn main:app --host 0.0.0.0 --port 10000
