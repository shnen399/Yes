import os
import random
import time
from typing import Dict, Tuple, List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# 讀帳號（支援逗號或換行分隔）
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    if not raw:
        return []
    parts: List[Tuple[str, str]] = []
    raw = raw.replace("\r", "\n")
    for seg in raw.replace(",", "\n").split("\n"):
        seg = seg.strip()
        if not seg or ":" not in seg:
            continue
        email, pwd = seg.split(":", 1)
        email, pwd = email.strip(), pwd.strip()
        if email and pwd:
            parts.append((email, pwd))
    return parts

def _env(name: str, default: str = "") -> str:
    v = os.getenv(name, "") or default
    return v.strip()

def post_article_once(keyword: str = "理債一日便") -> Dict:
    accounts = _read_accounts_from_env()
    if not accounts:
        return {"status": "fail", "error": "找不到帳號，請先設定 PIXNET_ACCOUNTS 環境變數"}

    email, password = random.choice(accounts)
    PIXNET_LOGIN_URL = _env("PIXNET_LOGIN_URL", "https://panel.pixnet.cc/")
    BLOG_HOST = _env("BLOG_HOST", "")
    HEADLESS = _env("HEADLESS", "true").lower() != "false"  # 預設 headless

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    title = f"{keyword} - 自動發文測試 {ts}"
    content_html = f"""
    <p>這是一篇自動發文測試文章（Playwright）。</p>
    <p>關鍵字：<strong>{keyword}</strong></p>
    <p>產生時間：{ts}</p>
    <p><a href="https://lihi.cc/japMO" target="_blank">理債一日便專屬連結</a></p>
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            ctx = browser.new_context(
                viewport={"width": 1366, "height": 860},
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
            )
            page = ctx.new_page()

            # 1) 登入
            page.goto(PIXNET_LOGIN_URL, wait_until="load", timeout=40000)
            try:
                sel_user = 'input[name="username"], input#username, input[type="email"]'
                sel_pass = 'input[name="password"], input#password, input[type="password"]'
                page.wait_for_selector(sel_user, timeout=15000)
                page.fill(sel_user, email)
                page.fill(sel_pass, password)
                try:
                    page.get_by_role("button", name="登入").click(timeout=3000)
                except Exception:
                    page.click('button[type="submit"]', timeout=3000)
            except PWTimeout:
                # 可能已經有登入狀態
                pass

            # 確認已進入 panel
            for _ in range(3):
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except PWTimeout:
                    pass
                if "panel.pixnet.cc" in page.url:
                    break
                page.goto("https://panel.pixnet.cc/", timeout=20000)

            # 2) 進入發文頁
            page.goto("https://panel.pixnet.cc/#/create-article", timeout=30000)
            page.wait_for_timeout(2500)

            # 3) 標題
            filled_title = False
            for sel in [
                'input[placeholder="請輸入文章標題"]',
                'input[placeholder*="標題"]',
                'input[type="text"]',
            ]:
                try:
                    page.fill(sel, title, timeout=3000)
                    filled_title = True
                    break
                except Exception:
                    continue
            if not filled_title:
                raise RuntimeError("找不到標題輸入框")

            # 4) 內文（常見 Quill/ProseMirror）
            editor_ok = False
            for sel in ["div.ql-editor", 'div[contenteditable="true"]', "div.ProseMirror"]:
                try:
                    page.eval_on_selector(sel, "(el, html) => el.innerHTML = html", content_html)
                    editor_ok = True
                    break
                except Exception:
                    continue
            if not editor_ok:
                raise RuntimeError("找不到內文編輯區")

            # 5) 發佈
            published = False
            for name in ["發佈", "發表", "發布", "發佈文章"]:
                try:
                    page.get_by_role("button", name=name).click(timeout=2000)
                    published = True
                    break
                except Exception:
                    continue
            if not published:
                try:
                    page.click('button:has-text("發佈")', timeout=2000)
                    published = True
                except Exception:
                    pass
            if not published:
                raise RuntimeError("找不到發佈按鈕")

            page.wait_for_timeout(5000)

            # 6) 嘗試抓文章連結
            link: Optional[str] = None
            try:
                link_el = page.query_selector("a[href*='pixnet.net/blog/post']")
                if link_el:
                    link = link_el.get_attribute("href")
            except Exception:
                pass

            # 7) 後備：文章列表
            if not link:
                try:
                    page.goto("https://panel.pixnet.cc/#/articles", timeout=20000)
                    page.wait_for_timeout(2000)
                    a = page.query_selector("a[href*='pixnet.net/blog/post']")
                    if a:
                        link = a.get_attribute("href")
                except Exception:
                    pass

            # 8) 再後備：BLOG 首頁
            if not link and BLOG_HOST:
                try:
                    page.goto(BLOG_HOST, timeout=20000)
                    page.wait_for_timeout(2000)
                    a = page.query_selector("a[href*='pixnet.net/blog/post']")
                    if a:
                        link = a.get_attribute("href")
                except Exception:
                    pass

            ctx.close()
            browser.close()

            return {
                "status": "success",
                "account": email,
                "title": title,
                "link": link or "未能自動抓到文章連結，請到部落格確認是否已發佈",
            }

    except Exception as e:
        return {"status": "fail", "account": email, "error": str(e)}
