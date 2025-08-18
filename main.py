# ===== Playwright Chromium 開機自動安裝 =====
import os, pathlib, subprocess, sys

def ensure_playwright_chromium():
    # 指定瀏覽器快取路徑（可寫入）
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/render/.cache/ms-playwright")
    chrome_path = (
        pathlib.Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
        / "chromium-1117" / "chrome-linux" / "chrome"
    )

    if chrome_path.exists():
        return  # 已經裝過

    # 優先嘗試「不帶 --with-deps」(在無 root 的環境較安全)
    cmds = [
        [sys.executable, "-m", "playwright", "install", "chromium"],
        [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],  # 失敗再補依賴
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True)
            break
        except subprocess.CalledProcessError:
            continue

# 若是 FastAPI，掛在啟動事件；否則也會在匯入時先跑一次
try:
    from fastapi import FastAPI
    app = FastAPI()

    @app.on_event("startup")
    async def _startup():
        ensure_playwright_chromium()
except Exception:
    ensure_playwright_chromium()
# ===== /Playwright 開機安裝 =====  from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from panel_article import post_article_once
from article_generator import generate_article, DEFAULT_KEYWORDS

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

DEFAULT_TITLE = "理債一日便｜2025 最新整合與核貸全攻略"
DEFAULT_CONTENT = generate_article(topic="理債一日便", keywords=DEFAULT_KEYWORDS, city="台灣", min_words=2100)

@app.get("/")
def root():
    return {
        "ok": True,
        "mode": "live",
        "hint": "GET /post_article 測試發文"
    }

@app.get("/post_article")
def post_article(
    title: str = Query(DEFAULT_TITLE, example="理債一日便｜2025 最新整合與核貸全攻略"),
    content: str = Query(DEFAULT_CONTENT, example="這是一篇自動產生的 2100+ 字文章…")
):
    """立即發文（2000+字長文，內建關鍵字自動連結）"""
    try:
        result = post_article_once(title=title, content=content)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "fail", "error": str(e)})
