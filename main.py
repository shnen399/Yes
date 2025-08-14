# main.py
import os
import asyncio
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ---- 可選：外部自帶的排程模組（沒有就略過）----
try:
    from scheduler import start_scheduler  # 如果你有寫就會啟動
except ImportError:
    start_scheduler = None

# ---- 建立 FastAPI ----
app = FastAPI(
    title="PIXNET 自動發文系統",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- 基本路由 ----
@app.get("/")
def root():
    return {"ok": True, "msg": "service alive"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/ping")
async def ping():
    return {"ok": True}

@app.post("/post_article")
def post_article():
    # TODO: 在這裡接上你的實際發文流程
    return {"status": "success", "message": "文章已發佈（測試）"}

# ---- 可選：啟動你自備的 scheduler ----
def _start_user_scheduler_if_any():
    if start_scheduler:
        try:
            start_scheduler()
            print("[scheduler] started")
        except Exception as e:
            print(f"[scheduler] 啟動失敗: {e}")

# ---- 可選：保活（Free 方案易休眠；有 RENDER_EXTERNAL_URL 時才啟動）----
BASE_URL: Optional[str] = os.getenv("RENDER_EXTERNAL_URL")  # 例如 https://yes-p512.onrender.com
INTERVAL_SEC = 300  # 每 5 分鐘

async def _keep_alive_loop(base_url: str):
    import httpx  # 放在函式內，避免缺套件時整個載入失敗
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                await client.get(f"{base_url}/ping")
                # print("keep-alive ok")  # 想看 log 再打開
            except Exception as e:
                # 不讓例外中斷迴圈
                print(f"[keep-alive] error: {e}")
            await asyncio.sleep(INTERVAL_SEC)

@app.on_event("startup")
async def on_startup():
    # 啟動你自帶的 scheduler（如果有）
    _start_user_scheduler_if_any()

    # 僅在偵測到外部網址時啟動保活
    if BASE_URL:
        asyncio.create_task(_keep_alive_loop(BASE_URL))
        print(f"[keep-alive] enabled -> {BASE_URL}/ping")
    else:
        print("[keep-alive] skipped (no RENDER_EXTERNAL_URL)")
