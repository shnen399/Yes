import os
import asyncio
import contextlib
import httpx
from fastapi import FastAPI

app = FastAPI(
    title="PIXNET 自動發文系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- 基本路由 ----
@app.get("/")
def home():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/ping")
async def ping():
    return {"ok": True}

@app.post("/post_article")
def post_article():
    # 這裡放你的發文邏輯（目前先回測試成功）
    return {"status": "success", "message": "文章已發佈（測試）"}

# ---- 保活任務（Free 方案避免休眠）----
# Render 會自動提供 RENDER_EXTERNAL_URL（例如 https://yes-p512.onrender.com）
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
INTERVAL_SEC = int(os.getenv("KEEPALIVE_INTERVAL", "270"))  # 預設 4.5 分鐘

async def keep_alive():
    if not BASE_URL:
        # 若本地啟動或沒提供外網 URL，就不做保活
        return
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            with contextlib.suppress(Exception):
                await client.get(f"{BASE_URL}/ping")
            await asyncio.sleep(INTERVAL_SEC)

@app.on_event("startup")
async def _startup():
    # 啟動背景任務（不阻塞主執行緒）
    asyncio.create_task(keep_alive())
