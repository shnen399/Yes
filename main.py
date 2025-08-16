# main.py
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio, traceback

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.0")

# 允許 CORS（Swagger / 手機測試都更順）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "msg": "Hello from PIXNET bot",
        "docs": "/docs",
        "test": "/test",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

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
    out = {}
    for k in keys:
        v = os.getenv(k)
        if v is None:
            out[k] = None
        elif k == "PIXNET_PASSWORD":
            out[k] = "********" if v else v
        else:
            out[k] = v
    return out

# 同一路徑同時支援 GET / POST，行動裝置用網址列測也可以
@app.api_route("/post_article", methods=["GET", "POST"])
async def post_article(keyword: str = Query(default="理債一日便", description="要發文的關鍵字/主題")):
    """
    觸發一次自動發文：
    - 會動態 import panel_article，呼叫 post_article_once(keyword)
    - 若找不到函式或出錯，回傳 {status: 'fail', step, error, trace}
    """
    try:
        # 動態載入，避免啟動時循環匯入
        try:
            mod = __import__("panel_article")
        except Exception as e:
            return {
                "status": "success",
                "result": {
                    "status": "fail",
                    "step": "import_module",
                    "error": f"無法匯入 panel_article：{e}",
                    "trace": traceback.format_exc(),
                },
            }

        func = getattr(mod, "post_article_once", None) or getattr(mod, "post_article", None)
        if not callable(func):
            return {
                "status": "success",
                "result": {
                    "status": "fail",
                    "step": "locate_function",
                    "error": "找不到 panel_article.post_article_once()",
                },
            }

        # 呼叫（支援同步/非同步）
        res = func(keyword=keyword) if "keyword" in getattr(func, "__code__", None).co_varnames else func(keyword)
        if asyncio.iscoroutine(res):
            res = await res

        # 確保是可序列化
        if isinstance(res, (str, int, float)) or res is None:
            res = {"data": res}

        return {"status": "success", "result": res}

    except Exception as e:
        # 統一錯誤格式，永遠回 JSON
        return {
            "status": "success",
            "result": {
                "status": "fail",
                "step": "runtime",
                "error": str(e),
                "trace": traceback.format_exc(),
            },
        }

@app.get("/test", response_class=HTMLResponse)
def test_page():
    # 測試頁：按鈕會呼叫 /post_article?keyword=xxx
    html = """
<!doctype html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8"/>
  <title>PIXNET 測試發文頁</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans TC', Arial, sans-serif; padding: 16px; }
    h2 { margin: 0 0 12px; }
    input, button { font-size: 16px; padding: 8px 12px; }
    #kw { width: 240px; }
    pre { background: #111; color: #0f0; padding: 12px; border-radius: 8px; overflow: auto; }
  </style>
</head>
<body>
  <h2>PIXNET 測試發文頁</h2>
  <div style="margin-bottom:12px;">
    <input id="kw" placeholder="輸入關鍵字，例如：理債一日便" value="理債一日便"/>
    <button onclick="postArticle()">測試發文</button>
  </div>
  <div id="status">就緒</div>
  <pre id="result">{}</pre>

<script>
async function postArticle() {
  const box = document.getElementById('result');
  const status = document.getElementById('status');
  const kw = document.getElementById('kw').value || '理債一日便';
  status.textContent = '發送中…';
  box.textContent = '';

  try {
    const resp = await fetch('/post_article?keyword=' + encodeURIComponent(kw), { method: 'POST' });
    const text = await resp.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = { raw: text };
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
    return HTMLResponse(content=html)
