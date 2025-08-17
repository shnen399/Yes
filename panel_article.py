import os
import random
import time
from typing import Dict, Tuple, List

from playwright.sync_api import sync_playwright

# ----------------------------------------------------
# 讀取帳號密碼（多帳號模式，從 PIXNET_ACCOUNTS 環境變數）
# ----------------------------------------------------
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    """
    環境變數格式：
    PIXNET_ACCOUNTS=email1:password1,email2:password2
    """
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    accounts = []
    for line in raw.split(","):
        if ":" in line:
            acc, pwd = line.split(":", 1)
            accounts.append((acc.strip(), pwd.strip()))
    return accounts


# ----------------------------------------------------
# 發文核心
# ----------------------------------------------------
def post_article_once(keyword: str = "理債一日便") -> Dict:
    accounts = _read_accounts_from_env()
    if not accounts:
        return {"status": "fail", "error": "找不到帳號，請先設定 PIXNET_ACCOUNTS 環境變數"}

    # 隨機挑一個帳號登入
    email, password = random.choice(accounts)

    title = f"{keyword} - 自動發文測試 {time.strftime('%Y-%m-%d %H:%M:%S')}"
    content = f"""
    <p>這是一篇自動發文測試文章。</p>
    <p>關鍵字：{keyword}</p>
    <p>產生時間：{time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><a href="https://lihi.cc/japMO">理債一日便專屬連結</a></p>
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            # 打開登入頁
            page.goto("https://panel.pixnet.cc/")
            page.fill('input[name="username"]', email)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle", timeout=15000)

            # 打開發文頁
            page.goto("https://panel.pixnet.cc/#/create-article")
            page.wait_for_timeout(3000)

            # 填標題 & 內文
            page.fill('input[placeholder="請輸入文章標題"]', title)
            page.fill('div.ql-editor', content)

            # 按下發布
            page.click('button:has-text("發佈")')
            page.wait_for_timeout(5000)

            # 嘗試抓取文章連結
            link = None
            try:
                link_el = page.query_selector("a[href*='pixnet.net/blog/post']")
                if link_el:
                    link = link_el.get_attribute("href")
            except:
                pass

            browser.close()

            return {
                "status": "success",
                "account": email,
                "title": title,
                "link": link or "未能抓到文章連結，請手動確認"
            }

    except Exception as e:
        return {"status": "fail", "account": email, "error": str(e)}
