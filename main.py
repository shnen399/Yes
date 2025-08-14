# main.py  — 只示範 /post_article 相關段落
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from panel_article import post_article_once  # 確保引用到上面的函式

log = logging.getLogger("pixnet")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

def _normalize_result(res: dict) -> dict:
    """
    兼容舊邏輯：不論 panel_article 回什麼格式，都盡量整理出 article_url。
    允許鍵名是 ok/success、url/article_url、acct/account 等。
    """
    if not isinstance(res, dict):
        return {"ok": False, "error": "Unknown result type."}

    ok = bool(res.get("ok", res.get("success", False)))
    article_url = res.get("article_url") or res.get("url") or res.get("link")
    title = res.get("title") or res.get("subject") or res.get("headline")
    account = res.get("account") or res.get("acct") or res.get("email")

    out = {"ok": ok, "article_url": article_url, "title": title, "account": account}
    if not ok:
        out["error"] = res.get("error") or res.get("message") or "發文失敗"
    return out

@app.post("/post_article")
def post_article():
    try:
        raw = post_article_once()
        data = _normalize_result(raw)

        if data["ok"] and data.get("article_url"):
            log.info("發文成功：%s  標題：%s  帳號：%s",
                     data["article_url"], data.get("title"), data.get("account"))
            return JSONResponse({
                "status": "ok",
                "message": "發文成功",
                "article_url": data["article_url"],
                "title": data.get("title"),
                "account": data.get("account"),
            })

        # 成功但沒抓到連結的情況（盡量提示）
        if data["ok"] and not data.get("article_url"):
            log.warning("發文可能成功，但未取得文章連結。原始回傳：%s", raw)
            return JSONResponse({
                "status": "partial",
                "message": "未取得文章連結，請查後台或檢查抓取邏輯。",
                "raw": raw,
            }, status_code=200)

        # 失敗
        log.error("發文失敗：%s", data.get("error"))
        return JSONResponse({
            "status": "fail",
            "error": data.get("error", "發文失敗"),
            "raw": raw,
        }, status_code=500)

    except Exception as e:
        log.exception("post_article 例外：%s", e)
        return JSONResponse({
            "status": "fail",
            "error": f"例外：{e.__class__.__name__}: {e}",
        }, status_code=500)
