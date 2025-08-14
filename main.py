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
