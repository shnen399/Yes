import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 嘗試匯入排程（沒有的話忽略）
try:
    from scheduler import start_scheduler
except ImportError:
    start_scheduler = None

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 啟動背景排程（如果有）
if start_scheduler:
    try:
        start_scheduler()
    except Exception as e:
        print(f"排程啟動失敗: {e}")

# 首頁路由
@app.get("/")
def home():
    return {"message": "PIXNET 自動發文系統已啟動"}

# 測試 API
@app.get("/ping")
def ping():
    return {"status": "ok"}

# 發文 API
@app.post("/post_article")
def post_article():
    # 這裡可以加你的自動發文邏輯
    return {"status": "success", "message": "文章已發佈（測試）"}
import os
import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI(title="PIXNET 自動發文", version="0.1.0")

# 你原本的路由 ...（/ 與 /healthz 與 /post_article 保留）

@app.get("/")
def root():
    return {"ok": True, "msg": "service alive"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# （可選）提供 /ping 端點給外部健康檢查或 cron 用
@app.get("/ping")
async def ping():
    return {"ok": True}

# ====== 下面是保活排程 ====== #
# Render 會自動提供 RENDER_EXTERNAL_URL，例如 https://yes-p512.onrender.com
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://yes-p512.onrender.com")
INTERVAL_SEC = 300  # 每 5 分鐘

async def keep_alive():
    # 用 async client 周期性打自己的根路由或 /ping
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                await client.get(BASE_URL)  # 也可改成 f"{BASE_URL}/ping"
            except Exception:
                # 不讓例外中斷迴圈
                pass
            await asyncio.sleep(INTERVAL_SEC)

@app.on_event("startup")
async def _startup():
    # 啟動背景任務（不阻塞主程式）
    asyncio.create_task(keep_alive())
