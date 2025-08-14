# main.py — 用 thread 執行同步版 Playwright，避免 asyncio 衝突
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import traceback

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 匯入你的同步函式（panel_article.py）
try:
    from panel_article import post_article_once  # 同步函式
except Exception as e:
    post_article_once = None  # type: ignore
    print("WARNING: cannot import panel_article.post_article_once:", e)

class PostReq(BaseModel):
    # 仍保留欄位（實作時會強制真發文）
    dry_run: bool | None = None
    timeout_sec: int | None = 180

@app.get("/")
def root():
    return {"status": "ok", "message": "PIXNET 自動發文系統已啟動", "docs": "/docs"}

@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})

def _run_blocking_real_post() -> dict:
    """
    在純同步環境下呼叫同步的 Playwright 實作。
    這個函式會被丟到 thread 裡執行，避免在事件迴圈裡觸發 Playwright 的偵測。
    """
    # 強制真發文（忽略外部 dry_run）
    try:
        try:
            return post_article_once(dry_run=False)  # type: ignore[arg-type]
        except TypeError:
            # 若你的 post_article_once 不接受參數
            return post_article_once()  # type: ignore[call-arg]
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "logs": []}

@app.post("/post_article")
async def post_article(_: PostReq | None = None):
    if post_article_once is None:
        return JSONResponse(
            status_code=500,
            content={"status": "fail", "error": "panel_article.post_article_once 不存在或匯入失敗"},
        )

    timeout = 180  # 可改成從 body 讀，但現在寫死即可
    loop = asyncio.get_running_loop()

    try:
        # 用 thread 執行同步 Playwright，避免「Sync API inside asyncio loop」錯誤
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _run_blocking_real_post),
            timeout=timeout,
        )

        if isinstance(result, dict) and result.get("ok"):
            return {"status": "ok", "result": result}
        else:
            return JSONResponse(status_code=502, content={"status": "fail", "result": result})

    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"status": "fail", "error": f"post_article timeout > {timeout}s"})
    except Exception:
        print("POST /post_article error:\n", traceback.format_exc())
        return JSONResponse(status_code=500, content={"status": "fail", "error": "internal error"})
