# panel_article.py
from typing import Dict, Any

def post_article_once() -> Dict[str, Any]:
    """
    執行一次發文，成功時請務必回傳 article_url。
    你原本的登入、填表、送出程式碼保持不變，只需要在成功後整理回傳。
    """
    # ====== 你的原本發文流程 ======
    # login(...)
    # create_article(...)
    # 取得成功後的文章網址，例如：
    # article_url = f"https://{blog_id}.pixnet.net/blog/post/{post_id}"
    # title = "你的文章標題"
    # used_account = "email@example.com"

    # --- 示意（請換成你實際取到的值） ---
    # article_url = real_article_url
    # title = real_title
    # used_account = real_account

    # ====== 成功回傳 ======
    return {
        "ok": True,
        "article_url": article_url,   # 務必是完整可點的 URL
        "title": title,
        "account": used_account,
        # 可加上更多欄位：published_at、tags、category...
    }

    # ====== 若失敗請回傳 ======
    # return {"ok": False, "error": "登入失敗/驗證碼錯誤/..."}
