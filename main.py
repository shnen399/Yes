# main.py
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.1")

# ---- CORS（保險起見，前端或 Swagger 皆可呼叫）----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 小工具 ----
def get_env_snapshot():
    # 讀環境變數；密碼打碼
    masked_pw = os.getenv("PIXNET_PASSWORD", "")
    if masked_pw:
        masked_pw = masked_pw[:2] + "******" + masked_pw[-2:]
    return {
        "PIXNET_EMAIL": os.getenv("PIXNET_EMAIL"),
        "PIXNET_PASSWORD": masked_pw,
        "PIXNET_LOGIN_URL": os.getenv("PIXNET_LOGIN_URL"),
        "PIXNET_NEW_ARTICLE_URL": os.getenv("PIXNET_NEW_ARTICLE_URL"),
        "PIXNET_TITLE_SELECTOR": os.getenv("PIXNET_TITLE_SELECTOR"),
        "PIXNET_ACCOUNTS": os.getenv("PIXNET_ACCOUNTS"),
        "PIXNET_MODE": os.getenv("PIXNET_MODE"),
        "BLOG_HOST": os.getenv("BLOG_HOST"),
        "NEWS_SOURCES": os.getenv("NEWS_SOURCES"),
    }

def ok(payload):
    return JSONResponse({"status": "success", **payload})

def fail(step: str, msg: str):
    return JSONResponse({"status": "success", "result": {"status": "fail", "step": step, "error": msg}})

# ---- 健康檢查 ----
@app.get("/health")
def health():
    return ok({"message": "ok"})

# ---- 檢查環境變數（完整）----
@app.get("/check_env_full")
def check_env_full():
    return ok(get_env_snapshot())

# ---- 發文 API：同時支援 GET 與 POST（關鍵修正）----
@app.api_route("/post_article", methods=["GET", "POST"])
async def post_article(request: Request, keyword: str = Query(default="理債一日便")):
    """
    這裡示範流程與檢查。實際自動化（登入/填表/送出）你可在這裡串接 Playwright 或 Selenium。
    目前先做參數與環境檢查，確保 API 流程通順，回傳固定格式 JSON。
    """
    # 若前端用 POST，但沒送 body，FastAPI 有時仍可；為避免 422，我們不強制 body。
    # 只要 method 正確即可繼續。
    env = get_env_snapshot()

    # 基本檢查：必要的 selector 與入口網址
    if not os.getenv("PIXNET_NEW_ARTICLE_URL"):
        return fail("env", "缺少發文入口：PIXNET_NEW_ARTICLE_URL")

    title_selector = os.getenv("PIXNET_TITLE_SELECTOR")
    if not title_selector:
        return fail("env", "缺少欄位選擇器：PIXNET_TITLE_SELECTOR")

    # 這裡本來會去做自動化。為了先確認路徑通了，回傳模擬結果。
    # 你未來把自動化結果塞進 result 就好。
    result = {
        "keyword": keyword,
        "note": "路徑 OK ─ 目前為示範回傳，尚未執行瀏覽器自動化。",
    }
    return ok({"result": {"status": "ok", **result}})

# ---- 測試頁（按按鈕 → 用 POST 呼叫 /post_article，固定回 JSON）----
@app.get("/test", response_class=HTMLResponse)
def test_page():
    html = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <title>PIXNET 測試發文頁</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans TC", Arial; padding: 16px; }
    button { padding: 10px 14px; border-radius: 8px; border: 1px solid #ddd; background:#fff; }
    #result { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #f8f9fa; padding: 12px; border-radius: 8px; border:1px solid #eee; }
    input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; }
    .row { margin: 12px 0; }
  </style>
</head>
<body>
  <h2>PIXNET 測試發文頁</h2>
  <div class="row">
    <label>keyword：</label>
    <input id="kw" placeholder="理債一日便" value="理債一日便" />
  </div>
  <div class="row">
    <button onclick="postArticle()">測試發文（POST）</button>
    <button onclick="getArticle()">測試發文（GET）</button>
  </div>
  <h4>結果：</h4>
  <pre id="result">尚未送出</pre>

<script>
async function postArticle(){
  const box = document.getElementById('result');
  const kw = document.getElementById('kw').value || '理債一日便';
  box.textContent = '發送中...';
  try{
    const resp = await fetch('/post_article?keyword=' + encodeURIComponent(kw), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}) // 給個空物件，避免部分環境 422
    });
    const data = await resp.json();
    box.textContent = JSON.stringify(data, null, 2);
  }catch(e){
    box.textContent = '請求錯誤：' + e;
  }
}

async function getArticle(){
  const box = document.getElementById('result');
  const kw = document.getElementById('kw').value || '理債一日便';
  box.textContent = '發送中...';
  try{
    const resp = await fetch('/post_article?keyword=' + encodeURIComponent(kw), { method: 'GET' });
    const data = await resp.json();
    box.textContent = JSON.stringify(data, null, 2);
  }catch(e){
    box.textContent = '請求錯誤：' + e;
  }
}
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
