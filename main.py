#  main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
import os
import inspect
from panel_article import post_article_once  # 從 panel_article.py 匯入發文主函式

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.0")


@app.get("/health")
def health():
    return {"message": "系統正常運作中"}


@app.get("/check_env_full")
def check_env_full():
    keys = [
        "PIXNET_EMAIL", "PIXNET_PASSWORD",
        "PIXNET_LOGIN_URL", "PIXNET_NEW_ARTICLE_URL",
        "PIXNET_TITLE_SELECTOR", "PIXNET_ACCOUNTS",
        "PIXNET_MODE", "BLOG_HOST", "NEWS_SOURCES",
    ]
    data = {}
    for k in keys:
        data[k] = os.getenv(k)
    return data


@app.post("/post_article")
async def post_article(keyword: str = "理債一日便"):
    """
    觸發一次自動發文，預設 keyword 為 "理債一日便"
    """
    try:
        if inspect.iscoroutinefunction(post_article_once):
            result = await post_article_once(keyword=keyword)
        else:
            result = post_article_once(keyword=keyword)
        return {"status": "success", "result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "fail", "error": str(e)})


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """
    提供一個測試頁面，上面有按鈕可以一鍵呼叫 /post_article
    """
    return """
<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><title>PIXNET 測試發文</title></head>
<body>
  <h2>PIXNET 測試發文頁</h2>
  <button onclick="postArticle()">測試發文</button>
  <pre id="result"></pre>
  <script>
    async function postArticle() {
      const box = document.getElementById('result');
      box.textContent = '發送中...';
      try {
        const res = await fetch('/post_article', {
          method: 'POST',
          headers: { 'Accept': 'application/json' }
        });
        const data = await res.json();
        box.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        box.textContent = '錯誤：' + e;
      }
    }
  </script>
</body>
</html>
"""
