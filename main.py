# main.py
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
# 預設 2100+ 字長文
DEFAULT_CONTENT = generate_article(topic="理債一日便", keywords=DEFAULT_KEYWORDS, city="台灣", min_words=2100)

@app.get("/")
def root():
    return {"ok": True, "hint": "GET /post_article 可立即測試發文（2000+字模板已內建）"}

@app.get("/post_article")
def post_article(
    title: str = Query(DEFAULT_TITLE),
    content: str = Query(DEFAULT_CONTENT),
    keywords: str = Query(",".join(DEFAULT_KEYWORDS)),
):
    kws = [k.strip() for k in keywords.split(",") if k.strip()]
    try:
        res = post_article_once(title=title, content=content, keywords=kws)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"status": "fail", "error": f"{e}"}, status_code=500)
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from panel_article import post_article_once

app = FastAPI(title="PIXNET 自動發文系統")

@app.get("/")
def root():
    mode = "live" if os.getenv("PIXNET_LIVE", "").strip() in {"1","true","True","YES","yes"} else "demo"
    return {"ok": True, "mode": mode, "hint": "GET /post_article 測試發文"}

@app.get("/check_env")
def check_env():
    live_raw = os.getenv("PIXNET_LIVE", "").strip()
    return {
        "PIXNET_LIVE": live_raw,
        "app_sees_live": live_raw in {"1","true","True","YES","yes"},
        "PIXNET_LOGIN_URL": os.getenv("PIXNET_LOGIN_URL",""),
    }

@app.get("/post_article")
def post_article():
    try:
        res = post_article_once()  # 內建模板
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"status":"error","error":str(e)}, status_code=500)
