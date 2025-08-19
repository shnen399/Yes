# ---- imports（若已有就不用重複）----
from typing import Optional, Dict
from fastapi import Query

# ---- 你的預設標題與內容（可自行修改）----
DEFAULT_TITLE = "理債一日便｜2025 最新整合與核貸全攻略"
DEFAULT_CONTENT = """
在現今的經濟環境中，許多人在資金調度時會首選「理債一日便」這類快速整合方案……
（此處放你原本那篇 2000+ 字的文章全文）
""".strip()

# ---- 路由：可選參數，若沒帶就用預設值 ----
@app.get("/post_article")
def post_article(
    title: Optional[str] = Query(None, description="文章標題（可省略，預設為 DEFAULT_TITLE）"),
    content: Optional[str] = Query(None, description="文章內容（可省略，預設為 DEFAULT_CONTENT）"),
    keywords: Optional[str] = Query(None, description="以逗號分隔的關鍵字，可省略"),
) -> Dict[str, str]:
    t = (title or DEFAULT_TITLE).strip()
    c = (content or DEFAULT_CONTENT).strip()
    ks = []
    if keywords:
        # 允許用逗號或全形逗號分隔
        ks = [k.strip() for k in keywords.replace("，", ",").split(",") if k.strip()]

    # 這裡呼叫你既有的發文函式（保持不動）
    # 例如：result = post_to_pixnet(title=t, content=c, keywords=ks)
    result = post_to_pixnet(title=t, content=c, keywords=ks)

    return {
        "status": "success" if result.get("ok") else "fail",
        "title": t,
        "url": result.get("url", ""),
        "hint": "未帶參數時會使用預設標題與長文內容",
    }
