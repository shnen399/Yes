# main.py — 直接接上真發文
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import traceback

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ---- 可選：如果你有 scheduler.py 就自動啟動 ----
try:
    from scheduler import start_scheduler  # type: ignore
except Exception:
    start_scheduler = None

if start_scheduler:
    try:
        start_scheduler()
    except Exception:
        pass

# ---- 連接你的發文模組 ----
# 預期 panel_article.py 內有 post_article_once()
try:
    from panel_article import post_article_once  # type: ignore
except Exception as e:  # 讓服務仍可啟動
    post_article_once = None  # type: ignore
    print("WARNING: 無法匯入 panel_article.post_article_once:", e)

# ---- 型別（可選參數，先保留彈性）----
class PostReq(BaseModel):
    dry_run: bool | None = None   # True=只測試不真的送出（若你的模組支援）
    timeout_sec: int | None = 120 # 逾時保護，避免卡死

@app.get("/")
def root():
    return {"status": "ok", "message": "PIXNET 自動發文系統已啟動", "docs": "/docs"}

@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})

@app.post("/post_article")
async def post_article(req: PostReq | None = None):
    if post_article_once is None:
        return JSONResponse(
            status_code=500,
            content={"status": "fail", "error": "找不到 panel_article.post_article_once，請確認檔案/函式存在。"}
        )

    timeout = (req.timeout_sec if req else None) or 120

    try:
        # 同時相容同步/非同步的 post_article_once
        async def _run():
            res = post_article_once() if not asyncio.iscoroutinefunction(post_article_once) else await post_article_once()
            return res

        result = await asyncio.wait_for(_run(), timeout=timeout)

        return {"status": "ok", "result": result}
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"status": "fail", "error": f"發文流程超過 {timeout} 秒未完成（timeout）。"}
        )
    except Exception as e:
        print("POST /post_article error:\n", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "fail", "error": f"{type(e).__name__}: {e}"}
        )
