# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ✅ 從 panel_article.py 匯入你的發文主函式
from panel_article import post_article_once

app = FastAPI(title="PIXNET 自動發文系統 - Swagger UI")

@app.get("/health")
def health():
    return {"message": "系統正常運作中"}

@app.get("/check_env")
def check_env():
    import os
    return {
        "PIXNET_EMAIL": os.getenv("PIXNET_EMAIL"),
        "PIXNET_MODE": os.getenv("PIXNET_MODE", "auto"),
        "ACCOUNTS_LINES": len([l for l in os.getenv("PIXNET_ACCOUNTS", "").splitlines() if l.strip()]) or 1,
    }

@app.get("/check_env_full")
def check_env_full():
    import os
    keys = [
        "PIXNET_EMAIL", "PIXNET_PASSWORD",
        "PIXNET_LOGIN_URL", "PIXNET_NEW_ARTICLE_URL",
        "PIXNET_TITLE_SELECTOR", "PIXNET_ACCOUNTS",
        "PIXNET_MODE", "BLOG_HOST", "NEWS_SOURCES",
    ]
    data = {}
    for k in keys:
        v = os.getenv(k)
        data[k] = v if (v and k not in {"PIXNET_PASSWORD"}) else v  # 可改成遮蔽密碼
    data["ACCOUNTS_LINES"] = len([l for l in os.getenv("PIXNET_ACCOUNTS", "").splitlines() if l.strip()])
    return data

@app.post("/post_article")
def post_article(keyword: str = "理債一日便"):
    """
    觸發一次自動發文。
    - keyword: 文章關鍵字（預設：理債一日便）
    """
    try:
        result = post_article_once(keyword)
        return {"status": "success", "result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "fail", "error": str(e)})
