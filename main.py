# main.py
from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List
import os

app = FastAPI(title="PIXNET 自動發文系統", version="1.0.0")


# --------- helpers ---------
def split_keywords(raw: Optional[str]) -> List[str]:
    """把關鍵字字串拆成陣列，支援中文頓號與半形逗號。"""
    if not raw:
        return []
    raw = raw.replace("，", ",").replace("、", ",")
    return [k.strip() for k in raw.split(",") if k.strip()]


def is_live_mode() -> bool:
    """環境變數 PIXNET_LIVE == '1' 視為 Live 發文模式。"""
    return str(os.getenv("PIXNET_LIVE", "0")).strip() == "1"


# --------- routes ----------
@app.get("/")
def root():
    mode = "live" if is_live_mode() else "demo"
    return {"ok": True, "mode": mode, "hint": 'GET "/post_article" 測試發文'}

@app.get("/check_env")
def check_env():
    mode = "live" if is_live_mode() else "demo"
    return {
        "ok": True,
        "mode": mode,
        "env": {
            "BLOG_HOST": os.getenv("BLOG_HOST"),
            "PIXNET_MODE": os.getenv("PIXNET_MODE"),
            "PLAYWRIGHT_BROWSERS_PATH": os.getenv("PLAYWRIGHT_BROWSERS_PATH"),
        },
    }

@app.get("/post_article")
def post_article(
    title: Optional[str] = Query(None, description="文章標題"),
    content: Optional[str] = Query(None, description="文章內容（可含HTML）"),
    # 支援兩種名稱，擇一使用即可
    keywords: Optional[str] = Query(None, description="關鍵字，逗號或頓號分隔"),
    keyword: Optional[str] = Query(None, description="關鍵字(別名)，逗號或頓號分隔"),
):
    # 基本驗證（避免 422）
    if not title:
        raise HTTPException(status_code=422, detail="title 必填")
    if not content:
        raise HTTPException(status_code=422, detail="content 必填")

    # 關鍵字處理：keywords 與 keyword 取其一（有給就合併）
    kw_source = ",".join([s for s in [keywords, keyword] if s])
    kw_list = split_keywords(kw_source)

    # 這裡先做示範：非 live 僅回傳 demo URL；live 時你可接上真實發文流程
    if is_live_mode():
        # TODO: 在這裡接你已經寫好的 PIXNET 真實發文流程
        # result_url = real_post_to_pixnet(title, content, kw_list)
        # return {"status": "success", "title": title, "url": result_url, "keywords": kw_list}
        return {
            "status": "success",
            "title": title,
            "keywords": kw_list,
            "url": "（此為示意，請接上真實發文結果 URL）",
            "hint": "目前為 LIVE 模式，但尚未串接真實發文函式。",
        }
    else:
        # DEMO：只回傳示意網址
        return {
            "status": "success",
            "title": title,
            "url": "https://www.pixnet.net/blog/post/123456-demo",
            "keywords": kw_list,
            "hint": "設定 PIXNET_LIVE=1 才會真的發文",
        }


# --------- dev entry (本地啟動用；在 Render 會由啟動命令啟動) ----------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
