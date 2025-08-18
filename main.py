from fastapi import FastAPI, Query
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
