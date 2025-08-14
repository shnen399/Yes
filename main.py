import os
import asyncio
import httpx
import logging
from typing import List, Tuple
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 嘗試匯入排程（沒有的話忽略）
try:
    from scheduler import start_scheduler
except ImportError:
    start_scheduler = None

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger(__name__)

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 從環境變數讀帳密
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    accounts = []
    for line in raw.splitlines():
        if ":" in line:
            email, pwd = line.strip().split(":", 1)
            accounts.append((email, pwd))
    return accounts

# API 路徑
@app.get("/")
def root():
    return {"message": "PIXNET Auto Poster 已啟動"}

@app.get("/post_article")
def manual_post():
    from post_to_pixnet import post_article_once
    res = post_article_once()
    return JSONResponse(content=res)

@app.get("/ping")
def ping():
    return {"status": "ok"}

# 啟動排程
if start_scheduler:
    try:
        start_scheduler()
    except Exception as e:
        log.error(f"啟動排程失敗: {e}")

# ---- keep-alive（避免 Render 免費版冷啟動）----
@app.on_event("startup")
async def _start_keepalive():
    base = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base:
        log.warning("未偵測到 RENDER
