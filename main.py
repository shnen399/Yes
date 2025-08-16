# main.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.0")

# CORS（測試用：全部打開）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可選：若你的發文流程寫在 panel_article.py
try:
    from panel_article import post_article_once  # def post_article_once(keyword: str) -> dict
except Exception:
    post_article_once = None


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/check_env_full")
def check_env_full():
    # 你原本的環境檢查內容可放這裡；先回一些關鍵 env 狀況
    import os
    return {
        "PIXNET_LOGIN_URL": os.getenv("PIXNET_LOGIN_URL"),
        "PIXNET_NEW_ARTICLE_URL": os.getenv("PIXNET_NEW_ARTICLE_URL"),
        "PIXNET_TITLE_SELECTOR": os.getenv("PIXNET_TITLE_SELECTOR"),
        "PIXNET_ACCOUNTS": os.getenv("PIXNET_ACCOUNTS"),
        "PIXNET_MODE": os.getenv("PIXNET_MODE"),
        "BLOG_HOST": os.getenv("BLOG_HOST"),
        "NEWS_SOURCES": os.getenv("NEWS_SOURCES"),
    }


@app.post("/post_article")
def post_article(keyword: str = Query(default="理債一日便")):
    """
    一律回 JSON，不讓前端誤判為 HTML。
    """
    # 真的有你的發文邏輯就呼叫；否則回覆友善訊息
    if post_article_once:
        try:
            result = post_article_once(keyword)  # 預期回 dict
            if not isinstance(result, dict):
                result = {"status": "fail", "step": "run", "error": "post_article_once 回傳非 dict"}
        except Exception as e:
            result = {"status": "fail", "step": "run", "error": f"{type(e).__name__}: {e}"}
    else:
        result = {
            "status": "fail",
            "step": "env",
            "error": "找不到 post_article_once（panel_article.py），請確認檔案與匯入。",
        }

    return JSONResponse({"status": "success", "result": result})


@app.get("/test", response_class=HTMLResponse)
def test_page():
    """
    簡易測試頁：按按鈕就呼叫 /post_article
    """
    html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <title>PIXNET 測試發文頁</title>
  <style>
    body { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; padding: 20px; }
    button { padding: 8px 12px; }
    input { padding: 6px 8px; width: 260px; }
    pre { white-space: pre-wrap; word-break: break-all; background:#111; color:#0f0; padding:12px; border-radius:8px; }
    .row { margin: 12px 0; }
  </style>
</head>
<body>
  <h2>PIXNET 測試發文頁</h2>

  <div class="row">
    <input id="kw" placeholder="關鍵字（預設：理債一日便）" />
    <button onclick="postArticle()">測試發文</button>
    <span id="status"></span>
  </div>

  <pre id="result">尚未測試</pre>

  <script>
  async function postArticle() {
    const box = document.getElementById('result');
    const status = document.getElementById('status');
    const kw = document.getElementById('kw').value || '理債一日便';

    status.textContent = '發送中…';
    box.textContent = '';

    try {
      const resp = await fetch('/post_article?keyword=' + encodeURIComponent(kw), {
        method: 'POST'
      });
      const text = await resp.text();

      let data;
      try {
        data = JSON.parse(text); // 優先當 JSON 解析
      } catch (e) {
        data = { raw: text };    // 若不是 JSON，直接顯示原文（避免 Unexpected token '<'）
      }

      box.textContent = JSON.stringify(data, null, 2);
      status.textContent = '完成';
    } catch (err) {
      box.textContent = JSON.stringify({ error: String(err) }, null, 2);
      status.textContent = '失敗';
    }
  }
  </script>
</body>
</html>
"""
    return HTMLResponse(html)
