from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
import os, json
from typing import Optional

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- helpers ---------------------------------------------------------------
def env_or(key: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(key)
    return val if val is not None and val != "" else default

def env_snapshot():
    keys = [
        "PIXNET_EMAIL",
        "PIXNET_PASSWORD",
        "PIXNET_LOGIN_URL",
        "PIXNET_NEW_ARTICLE_URL",
        "PIXNET_TITLE_SELECTOR",
        "PIXNET_TITLE_SELECTOR_ALT",
        "PIXNET_ACCOUNTS",
        "PIXNET_MODE",
        "BLOG_HOST",
        "NEWS_SOURCES",
    ]
    snap = {}
    for k in keys:
        snap[k] = env_or(k, None)
    return snap

# ---- routes ---------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "PIXNET 自動發文系統已啟動", "docs": "/docs", "test": "/test"}

@app.get("/favicon.ico")
def favicon():
    # 避免日誌一直 404
    return PlainTextResponse("", status_code=204)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/check_env_full")
def check_env_full():
    return JSONResponse(env_snapshot())

@app.get("/test")
def test_page():
    html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><title>PIXNET 測試發文頁</title></head>
<body>
  <h2>PIXNET 測試發文頁</h2>
  <input id="kw" value="理債一日便" />
  <button onclick="postArticle()">測試發文</button>
  <pre id="box">（結果會顯示在這）</pre>
<script>
async function postArticle(){
  const kw = document.getElementById('kw').value || '理債一日便';
  const res = await fetch(`/post_article?keyword=${encodeURIComponent(kw)}`, {method: 'POST'});
  const txt = await res.text();
  try { document.getElementById('box').textContent = JSON.stringify(JSON.parse(txt), null, 2); }
  catch(e){ document.getElementById('box').textContent = txt; }
}
</script>
</body>
</html>"""
    return HTMLResponse(html)

@app.api_route("/post_article", methods=["GET", "POST"])
def post_article(keyword: Optional[str] = Query(None), payload: Optional[dict] = Body(None)):
    # 同時支援 GET(Query) 與 POST(Body)
    kw = keyword
    if (not kw) and payload and isinstance(payload, dict):
        kw = payload.get("keyword")
    kw = kw or "理債一日便"

    # 這裡先提供示範回傳（不啟動瀏覽器自動化），確認 API/頁面串接無誤
    # 之後要接 Playwright/自動化，把下面 "note" 換成實作結果即可。
    result = {
        "狀態": "成功",
        "結果": {
            "帳號": "確定",
            "keyword": kw,
            "env": {
                "BLOG_HOST": env_or("BLOG_HOST"),
                "PIXNET_MODE": env_or("PIXNET_MODE", "auto"),
            }
        },
        "note": "路徑 OK — 目前為示範回傳，尚未執行瀏覽器自動化。"
    }
    return JSONResponse(result)
