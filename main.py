# main.py — 修正版（覆蓋用）

import os
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
# 預設就產生 2100+ 字長文；keywords 會自動連到固定 URL
DEFAULT_CONTENT = generate_article(
    topic="理債一日便",
    keywords=DEFAULT_KEYWORDS,
    city="台灣",
    min_words=2100
)


@app.get("/")
def root():
    return {
        "ok": True,
        "hint": "GET /post_article 以立即測試發文（2000+字長文模板已內建）"
    }


@app.get("/post_article")
def post_article(
    title: str = Query(DEFAULT_TITLE, example="理債一日便｜2025 最新整合與核貸全攻略"),
    content: str = Query(DEFAULT_CONTENT),
    keywords: str = Query(DEFAULT_KEYWORDS),
):
    """
    立即發文到 PIXNET（內容約 2000+ 字）
    """
    try:
        result = post_article_once(title=title, content=content, keywords=keywords)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"status": "fail", "error": str(e)})
