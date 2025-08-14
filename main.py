import os
from fastapi import FastAPI
from typing import List, Tuple

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

# 讀取多帳號
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    accounts = []
    for line in raw.splitlines():
        if ":" in line:
            email, pwd = line.strip().split(":", 1)
            accounts.append((email, pwd))
    return accounts

# 啟動排程
if start_scheduler:
    try:
        start_scheduler()
    except Exception as e:
        print(f"排程啟動失敗: {e}")

@app.get("/")
async def root():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.get("/test_accounts")
async def test_accounts():
    accounts = _read_accounts_from_env()
    return {"accounts": accounts}

@app.post("/post_article")
async def post_article():
    accounts = _read_accounts_from_env()
    if not accounts:
        return {"status": "fail", "error": "未偵測到帳號資訊"}
    # 這裡放發文邏輯
    return {"status": "success", "message": "測試發文完成"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
