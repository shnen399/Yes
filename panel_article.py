# panel_article.py — 真發文（Playwright）+ 安全回傳
from typing import Dict, Any, Optional, List, Tuple
import os, time, re
from datetime import datetime

# Playwright（在 Docker/Render 已安裝瀏覽器）
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ---- 工具 ----
def _pick_account() -> Tuple[str, str]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    if not raw:
        raise RuntimeError("環境變數 PIXNET_ACCOUNTS 未設定")
    first = raw.splitlines()[0].strip()
    if ":" not in first:
        raise RuntimeError("PIXNET_ACCOUNTS 格式錯誤，需為 email:password")
    email, pwd = first.split(":", 1)
    return email.strip(), pwd.strip()

def _gen_title() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"自動發文測試 {ts}"

def _gen_content() -> str:
    return (
        "<p>這是一篇由系統自動發佈的測試文章。</p>"
        '<p>理債一日便｜了解更多：<a href="https://lihi.cc/japMO" target="_blank">點我前往</a></p>'
        "<p>#自動發文 #測試</p>"
    )

# ---- 主要流程 ----
def post_article_once(dry_run: bool = False) -> Dict[str, Any]:
    logs: List[str] = []
    article_url: Optional[str] = None
    title: Optional[str] = None

    try:
        email, password = _pick_account()
        title = _gen_title()
        content_html = _gen_content()
        logs.append(f"account={email}")

        if dry_run:
            logs.append("dry_run=True，僅模擬回傳")
            return {
                "ok": True,
                "article_url": "https://example.com/article/123",
                "title": title,
                "error": None,
                "logs": logs,
            }

        # ---- 真的打開瀏覽器並發文 ----
        logs.append("launch chromium")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()

            # 直接進「寫文章」頁，未登入會被導到登入頁
            page.goto("https://panel.pixnet.cc/#/create-article", wait_until="networkidle", timeout=120_000)
            logs.append("goto create-article")

            # 登入（容錯：嘗試多種 placeholder / selector）
            try:
                # 常見輸入框
                email_in = page.get_by_placeholder("電子郵件").or_(page.locator('input[type="email"]'))
                pwd_in   = page.get_by_placeholder("密碼").or_(page.locator('input[type="password"]'))

                if email_in.count() == 0:
                    # 另一種後台版型
                    email_in = page.locator('input[name="email"]')
                if pwd_in.count() == 0:
                    pwd_in = page.locator('input[name="password"]')

                if email_in.count() > 0 and pwd_in.count() > 0:
                    email_in.first.fill(email, timeout=30_000)
                    pwd_in.first.fill(password, timeout=30_000)
                    # 送出登入
                    # 嘗試「登入」/「Sign in」按鈕
                    btn = page.get_by_role("button", name=re.compile("登入|Sign in|Log in", re.I))
                    if btn.count() == 0:
                        btn = page.get_by_text(re.compile("登入|Sign in|Log in", re.I))
                    btn.first.click(timeout=30_000)
                    logs.append("login submitted")
                    # 等待跳回寫文頁
                    page.wait_for_url(re.compile(r"panel\.pixnet\.cc/.+create-article"), timeout=60_000)
            except PWTimeout:
                # 可能已經保持登入狀態
                logs.append("login step timeout (可能已登入，繼續)")

            # 等待標題欄
            # 嘗試多種 selector：placeholder / name / role
            title_box = (
                page.get_by_placeholder(re.compile("文章標題|請輸入文章標題"))
                .or_(page.locator('input[name="title"]'))
                .or_(page.get_by_role("textbox").nth(0))
            )
            title_box.first.fill(title, timeout=30_000)
            logs.append("filled title")

            # 內容編輯器通常是 contenteditable；嘗試找第一個 contenteditable
            editor = page.locator('[contenteditable="true"]').first
            if editor.count() == 0:
                # 有些版型是 iframe（如 quill/tiptap），嘗試用 keyboard 輸入至聚焦處
                page.keyboard.press("Tab")
                time.sleep(0.3)
                page.keyboard.type("（自動輸入）", delay=10)
                logs.append("typed fallback content")
            else:
                # 直接注入 HTML（較穩）
                page.evaluate(
                    """(el, html) => { el.innerHTML = html; }""",
                    editor,
                    content_html,
                )
                logs.append("filled content")

            # 發佈按鈕（嘗試多種文字）
            publish_btn = page.get_by_role("button", name=re.compile("發佈|發布|Publish|Post", re.I))
            if publish_btn.count() == 0:
                publish_btn = page.get_by_text(re.compile("發佈|發布|Publish|Post", re.I))
            publish_btn.first.click(timeout=60_000)
            logs.append("clicked publish")

            # 發佈成功後通常會顯示成功提示或導向文章頁
            # 先等 URL 出現部落格網域
            try:
                page.wait_for_url(re.compile(r"(pixnet\.net/blog|pixnet\.cc/blog)"), timeout=90_000)
                article_url = page.url
                logs.append(f"redirected to article: {article_url}")
            except PWTimeout:
                # 若沒導過去，嘗試抓成功提示中的連結
                link = page.locator('a[href*="pixnet"]').first
                if link.count() > 0:
                    article_url = link.get_attribute("href")
                    logs.append(f"captured article link: {article_url}")

            # 關閉
            context.close()
            browser.close()

        if not article_url:
            return {
                "ok": False,
                "article_url": None,
                "title": title,
                "error": "publish failed: 無法取得文章連結（可能 selector 不符）",
                "logs": logs,
            }

        return {
            "ok": True,
            "article_url": article_url,
            "title": title,
            "error": None,
            "logs": logs,
        }

    except Exception as e:
        logs.append(f"exception: {type(e).__name__}: {e}")
        return {
            "ok": False,
            "article_url": article_url,
            "title": title,
            "error": f"{type(e).__name__}: {e}",
            "logs": logs,
        }
