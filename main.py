# main.py
import os
import json
import traceback
from typing import Tuple, List, Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

# 導入發文核心函式
from panel_article import post_article_once

# 如果有排程模組，啟動排程
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

if start_scheduler:
    try:
        start_scheduler()
    except Exception as e:
        print(f"排程啟動失敗：{e}")

# ---------------- 工具 ----------------
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    """
    從環境變數 PIXNET_ACCOUNTS 讀帳密，多行，每行 email:password
    """
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    out: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        email, pw = line.split(":", 1)
        out.append((email.strip(), pw.strip()))
    return out

def load_cookies() -> Optional[List[dict]]:
    """從 cookies.json 載入 cookies"""
    if not os.path.exists("cookies.json"):
        return None
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def to_playwright_cookies(cookies: List[dict]) -> List[dict]:
    """轉換 cookies 為 Playwright 格式"""
    out = []
    for c in cookies:
        if "name" in c and "value" in c:
            out.append({
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ""),
                "path": c.get("path", "/"),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", False),
                "sameSite": c.get("sameSite", "Lax")
            })
    return out

# ---------------- API ----------------
@app.get("/")
def root():
    return {"status": "ok", "msg": "PIXNET 自動發文系統已啟動"}

@app.get("/health")
def health():
    return PlainTextResponse("OK")

@app.post("/post_article")
async def api_post_article(payload: dict):
    """
    呼叫發文功能
    參數：
    - keyword: 用於生成文章內容的關鍵字
    - commit: True=直接發文; False=存草稿
    """
    keyword = payload.get("keyword", "").strip()
    will_commit = bool(payload.get("commit", False))

    if not keyword:
        return JSONResponse({"status": "fail", "error": "缺少 keyword"}, status_code=400)

    try:
        # 假設這裡你會生成 title 和 content
        title = f"{keyword} - 自動發文測試"
        content = f"<p>這是使用關鍵字「{keyword}」自動生成的測試內容。</p>"

        cookies_obj = load_cookies() or []
        play_cookies = to_playwright_cookies(cookies_obj)

        ok, url_or_msg = await post_article_once(
            cookies=play_cookies,
            title=title,
            content=content,
            commit=will_commit
        )

        mode = "POST_REAL" if will_commit else "SAVE_DRAFT"
        if ok:
            return {"status": "success", "mode": mode, "title": title, "url": url_or_msg}
        else:
            return {"status": "fail", "mode": mode, "title": title, "error": url_or_msg}

    except Exception as e:
        return JSONResponse(
            {
                "status": "fail",
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            status_code=500
        )
