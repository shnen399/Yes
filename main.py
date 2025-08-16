# main.py
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
import os

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.0")

# --- 安全匯入發文函式（避免匯入錯誤讓整個服務掛掉） ---
try:
    # 你專案裡負責實作發文流程的函式
    from panel_article import post_article_once  # noqa: F401
except Exception as e:
    # 若匯入失敗，用保護性實作回應錯誤（方便在 /check_env_full 看到問題）
    _panel_import_error = e

    def post_article_once(keyword: str):
        return {
            "status": "fail",
            "step": "env",
            "error": f"panel_article 載入失敗: {repr(_panel_import_error)}",
        }


# --- 基本健康檢查 ---
@app.get("/health", response_class=HTMLResponse)
def health():
    return "OK"


# --- 檢查環境變數（完整）---
@app.get("/check_env_full")
def check_env_full():
    keys = [
        "PIXNET_EMAIL",
        "PIXNET_PASSWORD",
        "PIXNET_LOGIN_URL",
        "PIXNET_NEW_ARTICLE_URL",
        "PIXNET_TITLE_SELECTOR",
        "PIXNET_ACCOUNTS",
        "PIXNET_MODE",
        "BLOG_HOST",
        "NEWS_SOURCES",
    ]
    envs = {k: os.getenv(k) for k in keys}
    # 額外提示 title selector 是否缺少
    if not envs.get("PIXNET_TITLE_SELECTOR"):
        envs["PIXNET_TITLE_SELECTOR"] = None
        envs["__HINT__"] = '缺少選擇器: PIXNET_TITLE_SELECTOR（例如：input[name="title"] 或 input[placeholder="請輸入文章標題"]）'
    return envs


# --- 發文：同時支援 GET / POST ---
# 用預設 keyword，手機上也能直接按 Execute 或用網址測
@app.get("/post_article")
@app.post("/post_article")
def post_article(
    request: Request,
    keyword: str = Query("理債一日便", description="要發的主題關鍵字"),
):
    """
    透過 GET 或 POST 觸發一次自動發文。
    瀏覽器可直接打：
    https://yes-6zei.onrender.com/post_article?keyword=理債一日便
    """
    result = post_article_once(keyword)
    # 統一回傳 JSON
    return JSONResponse(content={"status": "success", "result": result})


# --- 簡單測試頁：手機上也能一鍵觸發 ---
@app.get("/test", response_class=HTMLResponse)
def test_page(keyword: str = Query("理債一日便")):
    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <title>PIXNET 測試發文頁</title>
</head>
<body>
  <h2>PIXNET 測試發文頁</h2>
  <button onclick="postArticle()">測試發文</button>
  <pre id="result">（尚未執行）</pre>

<script>
async function postArticle() {{
  const box = document.getElementById('result');
  box.textContent = "發送中…";
  try {{
    const url = '/post_article?keyword=' + encodeURIComponent('{keyword}');
    const res = await fetch(url, {{ method: 'GET' }});
    const data = await res.json();
    box.textContent = JSON.stringify(data, null, 2);
  }} catch (err) {{
    box.textContent = '發送失敗: ' + err;
  }}
}}
</script>
</body>
</html>
"""
    return HTMLResponse(html)
