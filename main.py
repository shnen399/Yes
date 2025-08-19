from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import os
import urllib.parse
import logging

app = FastAPI(title="PIXNET 自動發文系統", version="1.0.1")

# 日誌設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("pixnet")

# 假裝的發文器（你原本的實作可接回來）
def post_to_pixnet(title: str, content: str, keywords: list[str]) -> str:
    """
    回傳發文後的文章連結（DEMO 用，實際可替換成你原本的函式）
    """
    # 這裡只是示範，照你的原本流程去發文即可
    return "https://www.pixnet.net/blog/post/123456-demo"

@app.get("/", response_class=JSONResponse)
def root():
    mode = "live" if os.getenv("PIXNET_LIVE") == "1" else "demo"
    return {"ok": True, "mode": mode, "hint": 'GET "/post_article" 測試發文'}

@app.get("/favicon.ico", response_class=PlainTextResponse)  # 擋掉 404 噪音
def favicon():
    return ""

@app.get("/check_env", response_class=JSONResponse)
def check_env():
    return {
        "PIXNET_LIVE": os.getenv("PIXNET_LIVE", "0"),
        "HEADLESS": os.getenv("HEADLESS", "true"),
    }

@app.get("/post_article", response_class=JSONResponse)
def post_article(
    title: str = Query(..., description="文章標題"),
    content: str = Query(..., description="文章內容"),
    keywords: str = Query("", description="以逗號分隔的關鍵字"),
):
    """
    注意：keywords 請用「逗號分隔的字串」，例如：
    理債一日便最新核貸流程, 理債一日便申請條件, 貸款技巧
    """
    try:
        # 乾淨的 log（把網址編碼還原）
        pretty_title = urllib.parse.unquote_plus(title)
        pretty_content = urllib.parse.unquote_plus(content)
        pretty_keywords = urllib.parse.unquote_plus(keywords)

        # 解析關鍵字：逗號分隔 → list
        kw_list = [k.strip() for k in pretty_keywords.split(",") if k.strip()]

        # 呼叫你的發文流程
        url = post_to_pixnet(pretty_title, pretty_content, kw_list)

        # 乾淨輸出
        log.info("✅ 發文成功")
        log.info(f"標題：{pretty_title}")
        log.info(f"網址：{url}")

        return {
            "status": "success",
            "title": pretty_title,
            "url": url,
            "hint": '設定 PIXNET_LIVE=1 才會真的發文',
        }
    except Exception as e:
        log.info("❌ 發文失敗")
        log.exception(e)
        return {
            "status": "fail",
            "error": str(e),
        }
