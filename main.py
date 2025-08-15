from fastapi import Request, HTTPException
from panel_article import post_article_once  # ← 確保有這行

def _to_bool(v: str) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

@app.post("/post_article")
async def post_article(request: Request):
    """
    產文並（可選）發佈到痞客邦
    body 可傳：
      {
        "keyword": "理財一日便",   # 可選
        "commit": true           # 可選，true/1/yes 才會真的發文
      }
    也可用 query：/post_article?keyword=xxx&commit=1
    """
    # 讀 body（可能為空）
    try:
        data = await request.json()
    except Exception:
        data = {}

    # 參數：keyword / commit
    keyword = (data.get("keyword")
               or request.query_params.get("keyword")
               or "").strip()

    # commit：query > body > 環境變數（預設 False）
    commit_q = request.query_params.get("commit")
    commit_b = data.get("commit")
    commit_env = os.getenv("ALLOW_POST", "0")
    commit = (
        _to_bool(commit_q) if commit_q is not None else
        _to_bool(commit_b) if isinstance(commit_b, (str, int, bool)) else
        _to_bool(commit_env)
    )

    # 先檢查帳號是否存在
    accounts = _read_accounts_from_env()
    if not accounts:
        raise HTTPException(status_code=400, detail="未偵測到 PIXNET 帳號，請先設定環境變數 PIXNET_ACCOUNTS")

    # 呼叫真正產文/發文流程
    try:
        result = post_article_once(keyword=keyword, commit=commit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"post_article_once 失敗: {e}")

    mode = "POST_REAL" if commit else "PREVIEW_ONLY"
    return {
        "status": "success",
        "mode": mode,
        "input_keyword": keyword,
        "result": result
    }
