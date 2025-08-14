# panel_article.py — 真發文（Playwright）+ 安全回傳
from typing import Dict, Any, Optional, List, Tuple
import os, time, re
from datetime import datetime

# Playwright（在 Docker/Render 已安裝瀏覽器）
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ---- 環境變數 ----
# 多帳號可用多行： email:password
ENV_ACCOUNTS = os.getenv("PIXNET_ACCOUNTS", "").strip()
# 若要改目標頁，可改這個（預設直接進寫文頁）
TARGET_CREATE_URL = os.getenv("PIXNET_CREATE_URL", "https://panel.pixnet.cc/#/create-article")

# ---- 工具 ----
def _pick_account() -> Tuple[str, str]:
    """從環境變數抓第一組帳密 email:password"""
    if not ENV_ACCOUNTS:
        raise RuntimeError("環境變數 PIXNET_ACCOUNTS 未設定")
    first = ENV_ACCOUNTS.splitlines()[0].strip()
    if ":" not in first:
        raise RuntimeError("PIXNET_ACCOUNTS 格式錯誤，需為 email:password")
    email, pwd = first.split(":", 1)
    return email.strip(), pwd.strip()

def _gen_title() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"自動發文測試 {ts}"

def _gen_content() -> str:
    # 你可自訂內容（HTML）
    return (
        "<p>這是一篇由系統自動發佈的測試文章。</p>"
        '<p>理債一日便｜了解更多：<a href="https://lihi.cc/japMO" target="_blank">點我前往</a></p>'
        "<p>#自動發文 #測試</p>"
    )

# ---- 主要流程 ----
def post_article_once(dry_run: bool = False) -> Dict[str, Any]:
    """
    自動登入 PIXNET 後台 -> 建立文章 -> 發佈
    回傳：
    {
      ok: bool,
      article_url: Optional[str],
      title: Optional[str],
      error: Optional[str],
      logs: List[str]
    }
    """
    logs: List[str] = []
    article_url: Optional[str] = None
    title: Optional[str] = None

    try:
        email, password = _pick_account()
        title = _gen_title()
        content_html = _gen_content()
        logs.append("picked account")

        if dry_run:
            logs.append("dry_run=True（僅模擬，不發文）")
            return {
                "ok": True,
                "article_url": "https://example.com/article/123",
                "title": title,
                "error": None,
                "logs": logs,
            }

        # ---- 真的打開瀏覽器並發文 ----
        logs.append("launching chromium")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()

            # 直接進「寫文章」頁，未登入會被導到登入頁
            page.goto(TARGET_CREATE_URL, wait_until="networkidle", timeout=120_000)
            logs.append("goto create-article")

            # ===== 登入流程（容錯多 selector）=====
            try:
                # 常見輸入框（placeholder/類型/name 都嘗試）
                email_in = (
                    page.get_by_placeholder(re.compile("電子郵件|email", re.I))
                    .or_(page.locator('input[type="email"]'))
                    .or_(page.locator('input[name="email"]'))
                )
                pwd_in = (
                    page.get_by_placeholder(re.compile("密碼|password", re.I))
                    .or_(page.locator('input[type="password"]'))
                    .or_(page.locator('input[name="password"]'))
                )

                if email_in.count() > 0 and pwd_in.count() > 0:
                    email_in.first.fill(email, timeout=30_000)
                    pwd_in.first.fill(password, timeout=30_000)
                    # 送出登入（button 或純文字）
                    btn = page.get_by_role("button", name=re.compile("登入|Sign in|Log in", re.I))
                    if btn.count() == 0:
                        btn = page.get_by_text(re.compile("登入|Sign in|Log in", re.I))
                    btn.first.click(timeout=30_000)
                    logs.append("login submitted")
                    # 等待跳回寫文頁
                    page.wait_for_url(re.compile(r"panel\.pixnet\.cc/.+create-article"), timeout=60_000)
                else:
                    logs.append("login fields not found（可能已登入）")
            except PWTimeout:
                # 可能已經保持登入狀態
                logs.append("login step timeout（可能已登入，繼續）")

            # ===== 填標題 =====
            title_box = (
                page.get_by_placeholder(re.compile("文章標題|請輸入文章標題"))
                .or_(page.locator('input[name="title"]'))
                .or_(page.get_by_role("textbox").nth(0))
            )
            if title_box.count() == 0:
                raise RuntimeError("找不到標題欄位 selector")
            title_box.first.fill(title, timeout=30_000)
            logs.append("filled title")

            # ===== 填內容 =====
            # 常見富文字編輯器會是 contenteditable 區塊；先試這個
            editor = page.locator('[contenteditable="true"]').first
            if editor.count() > 0:
                page.evaluate("""(el, html) => { el.innerHTML = html; }""", editor, content_html)
                logs.append("filled content via contenteditable")
            else:
                # 有些是 iframe 編輯器：先嘗試 focus 再以鍵盤輸入備援
                page.keyboard.press("Tab")
                time.sleep(0.2)
                page.keyboard.type("（自動輸入內容備援）" + re.sub(r"<.*?>", "", content_html), delay=10)
                logs.append("typed fallback content")

            # ===== 發佈 =====
            publish_btn = page.get_by_role("button", name=re.compile("發佈|發布|Publish|Post", re.I))
            if publish_btn.count() == 0:
                publish_btn = page.get_by_text(re.compile("發佈|發布|Publish|Post", re.I))
            if publish_btn.count() == 0:
                raise RuntimeError("找不到發佈按鈕")
            publish_btn.first.click(timeout=60_000)
            logs.append("clicked publish")

            # 發佈後通常會導向文章頁或顯示成功連結
            try:
                page.wait_for_url(re.compile(r"(pixnet\.net/blog|pixnet\.cc/blog)"), timeout=90_000)
                article_url = page.url
                logs.append(f"redirected to article: {article_url}")
            except PWTimeout:
                link = page.locator('a[href*="pixnet"]').first
                if link.count() > 0:
                    article_url = link.get_attribute("href")
                    logs.append(f"captured article link: {article_url}")
                else:
                    logs.append("no redirect or link captured")

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
