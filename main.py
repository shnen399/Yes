# main.py — 覆蓋版
import os
from typing import List, Optional, Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# 可選：有排程就啟動，沒有也不影響
try:
    from scheduler import start_scheduler  # type: ignore
except Exception:
    start_scheduler = None  # 沒有就略過

# 可選：匯入實際發文函式；若沒有，提供安全替代
try:
    from panel_article import post_article_once  # type: ignore
except Exception:
    def post_article_once(*args, **kwargs) -> Dict[str, Any]:
        # 沒有真實模組時的安全回傳，方便檢查 API 是否通
        return {"mock": True, "msg": "panel_article.post_article_once 未載入"}

app = FastAPI(
    title="FastAPI",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 啟動背景排程（如果有）
if start_scheduler:
    try:
        start_scheduler()
    except Exception:
        pass


# ---------- 型別定義 ----------
class PostPayload(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = []


# ---------- 路由 ----------
@app.get("/")
def root():
    return {"ok": True, "msg": "Anti-translate Playwright install works on Render"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/post_article")
def post_article(payload: PostPayload):
    """
    嘗試呼叫 panel_article.post_article_once。
    若該函式需要參數就傳入；若簽名不同會再以無參數呼叫一次。
    """
    try:
        # 優先帶參數呼叫（支援 title/content/tags）
        result = post_article_once(
            **{k: v for k, v in payload.dict().items() if v not in (None, [], {})}
        )
    except TypeError:
        # 若函式不吃參數，改用無參數呼叫（舊版相容）
        result = post_article_once()

    return JSONResponse(
        content={
            "status": "success",
            "result": result
        }
    )
