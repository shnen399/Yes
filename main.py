import os
from typing import List, Tuple
from fastapi import FastAPI

# 嘗試匯入排程（若沒有就略過）
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

# 讀取多帳號（環境變數 PIXNET_ACCOUNTS，每行 email:password）
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    accounts = []
    for line in raw.splitlines():
        if ":" in line:
            email, pwd = line.strip().split(":", 1)
            accounts.append((email, pwd))
    return accounts

# 啟動排程（若有）
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

# ✅ GET + POST 都能觸發
@app.get("/post_article")
@app.post("/post_article")
async def post_article():
    accounts = _read_accounts_from_env()
    if not accounts:
        return {"status": "fail", "error": "未偵測到帳號資訊（請設定 PIXNET_ACCOUNTS）"}
    # TODO: 在這裡放真正發文邏輯
    return {"status": "success", "message": "測試發文完成"}
