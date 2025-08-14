# main.py — 連 panel_article 並完整回傳結果
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

# 可選：啟動排程
try:
    from scheduler import start_scheduler  # type: ignore
except Exception:
    start_scheduler = None
if start_scheduler:
    try:
        start_scheduler()
    except Exception:
        pass

# 連你的發文函式
try:
    from panel_article import post_article_once  # type: ignore
except Exception as e:
    post_article_once = None  # type: ignore
    print("WARNING: cannot import panel_article.post_article_once:", e)

class PostReq(BaseModel):
    dry_run: bool | None = None
    timeout_sec: int | None = 180

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
            content={"status": "fail", "error": "panel_article.post_article_once 不存在或匯入失敗"},
        )

    timeout = (req.timeout_sec if req else None) or 180

    try:
        async def _run():
            if asyncio.iscoroutinefunction(post_article_once):
                return await post_article_once()
            return post_article_once()

        result = await asyncio.wait_for(_run(), timeout=timeout)

        # 期望 result 具有 ok/article_url/title/error/logs
        if isinstance(result, dict) and result.get("ok"):
            return {"status": "ok", "result": result}
        else:
            # 失敗時也把詳情帶回
            return JSONResponse(status_code=502, content={"status": "fail", "result": result})

    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"status": "fail", "error": f"post_article timeout > {timeout}s"},
        )
    except Exception as e:
        print("POST /post_article error:\n", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "fail", "error": f"{type(e).__name__}: {e}"},
        )
