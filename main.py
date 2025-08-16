# main.py  — Render 可直接部署版
import os
from typing import List, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 可選：有就啟動排程，沒有就略過
try:
    from scheduler import start_scheduler  # type: ignore
except Exception:
    start_scheduler = None  # 沒有這個模組也 OK

# 可選：提供手動發文端點（若有這個函式）
try:
    from panel_article import post_article_once  # type: ignore
except Exception:
    post_article_once = None  # 沒有就略過

app = FastAPI(
    title="PIXNET 自動發文系統",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- 工具函式 ----
def _parse_accounts(env_text: str) -> List[Dict[str, str]]:
    """
    將 PIXNET_ACCOUNTS 多行字串解析為帳號清單。
    允許格式：每行 `email:password`；會忽略空白行與無冒號的行。
    """
    out: List[Dict[str, str]] = []
    if not env_text:
        return out
    for line in env_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        email, pwd = line.split(":", 1)
        out.append({"email": email.strip(), "password": pwd.strip()})
    return out


# ---- 啟動排程（若有）----
if start_scheduler:
    try:
        start_scheduler()
    except Exception:
        # 排程啟動失敗不影響 API
        pass


# ---- API ----
@app.get("/")
def root():
    return {
        "name": "PIXNET 自動發文系統",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/check_env", summary="Check Env")
def check_env():
    """
    回傳與 PIXNET 相關的關鍵環境變數（簡版）
    兼容舊版只用 PIXNET_EMAIL / PIXNET_PASSWORD 的情況
    """
    return {
        "PIXNET_EMAIL": os.getenv("PIXNET_EMAIL", ""),
        "PIXNET_PASSWORD": os.getenv("PIXNET_PASSWORD", ""),
        "PIXNET_MODE": os.getenv("PIXNET_MODE", ""),
        "ACCOUNTS_LINES": len(os.getenv("PIXNET_ACCOUNTS", "").strip().splitlines())
        if os.getenv("PIXNET_ACCOUNTS")
        else 0,
    }


@app.get("/check_env_full", summary="Check Env Full")
def check_env_full():
    """
    解析多組帳號（PIXNET_ACCOUNTS）並詳細列出。
    其他有用的設定也一併回傳，方便除錯。
    """
    accounts_raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    accounts = _parse_accounts(accounts_raw)

    return {
        "accounts_count": len(accounts),
        "accounts": accounts,  # 若要避免顯示密碼，可只回傳 email
        "legacy_email": os.getenv("PIXNET_EMAIL", ""),
        "legacy_password_set": bool(os.getenv("PIXNET_PASSWORD")),
        "PIXNET_MODE": os.getenv("PIXNET_MODE", ""),
        "PIXNET_LOGIN_URL": os.getenv("PIXNET_LOGIN_URL", ""),
        "PIXNET_NEW_ARTICLE_URL": os.getenv("PIXNET_NEW_ARTICLE_URL", ""),
        "BLOG_HOST": os.getenv("BLOG_HOST", ""),
        "NEWS_SOURCES": os.getenv("NEWS_SOURCES", ""),
    }


# （可選）手動發文端點：如果專案有 post_article_once，就開放測試
@app.post("/post_article", summary="Post one article (if supported)")
def post_article():
    if not post_article_once:
        return JSONResponse(
            {"status": "fail", "error": "post_article_once 未提供或模組不存在"}, status_code=400
        )
    try:
        result = post_article_once()
        return {"status": "ok", "result": result}
    except Exception as e:
        return JSONResponse(
            {"status": "fail", "error": f"{type(e).__name__}: {e}"}, status_code=500
        )
