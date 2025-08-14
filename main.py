# main.py  — 覆蓋版
import os
from typing import Optional, Tuple, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 可選：如果你有 scheduler.py，就會啟動排程；沒有也不影響
try:
    from scheduler import start_scheduler  # type: ignore
except Exception:
    start_scheduler = None

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 啟動背景排程（如果存在）
if start_scheduler:
    try:
        start_scheduler()
    except Exception:
        pass


@app.get("/")
def root():
    """
    首頁健康檢查：打開 Render 主網址時會看到這段 JSON，不會再 404。
    """
    return {
        "status": "ok",
        "message": "PIXNET 自動發文系統已啟動",
        "docs": "/docs",
    }


@app.get("/healthz")
def healthz():
    """給 Render 健康檢查用"""
    return JSONResponse({"ok": True})


# ---- 如果你已有單次發文 API，可保留或改成你現有的實作 ----
@app.post("/post_article")
def post_article():
    """
    範例：回傳成功訊息；你可替換成真正的發文流程。
    """
    return {"status": "ok", "detail": "已觸發發文（示範）"}
