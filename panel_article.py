import os
import datetime as dt
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, TimeoutError as PWTimeout


# ---- 讀取環境變數（需在 Render/本機 .env 設好）----
PIXNET_EMAIL = os.getenv("PIXNET_EMAIL")
PIXNET_PASSWORD = os.getenv("PIXNET_PASSWORD")

# 預設登入與發文頁面（可覆蓋）
PIXNET_LOGIN_URL = os.getenv("PIXNET_LOGIN_URL", "https://member.pixnet.net/login")
PIXNET_NEW_ARTICLE_URL = os.getenv("PIXNET_NEW_ARTICLE_URL", "https://panel.pixnet.cc/blog/articles/new")

# 標題與內文的 CSS Selector（可覆蓋）
# 建議你已經新增：
#   PIXNET_TITLE_SELECTOR='input[placeholder="請輸入文章標題"]'
# 若沒有，下面會自動用一組候補 selector 嘗試。
ENV_TITLE_SELECTOR = os.getenv("PIXNET_TITLE_SELECTOR", "").strip()

# 這個是常見的候補 selector 清單（從你的後台截圖推斷）
TITLE_SELECTOR_FALLBACKS: List[str] = [
    ENV_TITLE_SELECTOR,                      # 你環境變數指定的
    'input[placeholder="請輸入文章標題"]',    # 痞客邦新版編輯器
    'input[name="title"]',
    'input#title',
]

# 內文：痞客邦後台常是 iframe 內的 contenteditable 區域（不同版本會換）
# 這裡會在所有 iframe 裡找 contenteditable 的元素當作編輯器
CONTENT_EDITABLE_CANDIDATES = [
    '[contenteditable="true"]',
    '.tox-edit-area__iframe',       # TinyMCE 容器 iframe（舊版）
    '#tinymce',                     # TinyMCE 內文（iframe 內）
    'textarea',                     # 最保底
]

PUBLISH_BUTTON_CANDIDATES = [
    'text=發表公開文章',
    'button:has-text("發表")',
    'button:has-text("公開")',
    'text=發佈',
]

SAVE_DRAFT_BUTTONS = [
    'text=儲存草稿',
    'button:has-text("儲存草稿")',
]


def _today_tag():
    return dt.datetime.now().strftime("%Y-%m-%d")


async def post_to_pixnet(keyword: str) -> Dict:
    """
    自動登入 → 新增文章 → 發佈（或草稿）並回傳結果。
    """
    if not PIXNET_EMAIL or not PIXNET_PASSWORD:
        return {
            "狀態": "失敗",
            "步驟": "init",
            "error": "缺少 PIXNET_EMAIL 或 PIXNET_PASSWORD 環境變數",
        }

    title = f"{keyword}｜自動發文測試 {_today_tag()}"
    content = (
        f"<p>這是一篇由系統自動產生的測試文（關鍵字：{keyword}）。</p>"
        f"<p>建立時間：{dt.datetime.now():%Y-%m-%d %H:%M:%S}</p>"
    )

    async with async_playwright() as p:
        # Render 上建議 headless=True
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1) 登入
            await page.goto(PIXNET_LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

            # 嘗試填入帳密（列幾種常見 selector）
            email_selectors = ['input[type="email"]', 'input[name="email"]', '#email', '#login-username', 'input[autocomplete="username"]']
            pwd_selectors = ['input[type="password"]', 'input[name="password"]', '#password', '#login-pass', 'input[autocomplete="current-password"]']
            login_btns    = ['button:has-text("登入")', 'text=登入', 'button[type="submit"]']

            # email
            filled = False
            for sel in email_selectors:
                try:
                    await page.fill(sel, PIXNET_EMAIL, timeout=3_000)
                    filled = True
                    break
                except:
                    pass
            if not filled:
                raise RuntimeError("找不到帳號輸入框")

            # password
            filled = False
            for sel in pwd_selectors:
                try:
                    await page.fill(sel, PIXNET_PASSWORD, timeout=3_000)
                    filled = True
                    break
                except:
                    pass
            if not filled:
                raise RuntimeError("找不到密碼輸入框")

            # click login
            clicked = False
            for sel in login_btns:
                try:
                    await page.click(sel, timeout=3_000)
                    clicked = True
                    break
                except:
                    pass
            if not clicked:
                # 有些頁面按 Enter 就能送出
                await page.keyboard.press("Enter")

            # 等待登入成功（轉到後台或有會員狀態）
            try:
                await page.wait_for_load_state("networkidle", timeout=20_000)
            except PWTimeout:
                pass

            # 2) 新增文章頁
            await page.goto(PIXNET_NEW_ARTICLE_URL, wait_until="domcontentloaded", timeout=60_000)

            # 2-1) 填標題
            title_ok = False
            for sel in TITLE_SELECTOR_FALLBACKS:
                if not sel:
                    continue
                try:
                    await page.fill(sel, title, timeout=4_000)
                    title_ok = True
                    break
                except:
                    continue

            if not title_ok:
                # 再退而求其次，找任何可輸入的 input
                try:
                    await page.fill("input[type='text']", title, timeout=3_000)
                    title_ok = True
                except:
                    pass

            if not title_ok:
                raise RuntimeError("找不到可用的標題輸入框（title selector）")

            # 2-2) 填內文（多半在 iframe）
            content_ok = False

            # 先找所有 iframe，一個個切進去找 contenteditable
            for frame in page.frames:
                try:
                    for candidate in CONTENT_EDITABLE_CANDIDATES:
                        try:
                            await frame.fill(candidate, content, timeout=2_000)
                            content_ok = True
                            break
                        except:
                            # 有些是 contenteditable 不能用 fill，用 evaluate 設 innerHTML
                            try:
                                el = await frame.query_selector(candidate, timeout=1_000)
                                if el:
                                    await frame.evaluate(
                                        '(e, html) => { e.innerHTML = html; }',
                                        el, content
                                    )
                                    content_ok = True
                                    break
                            except:
                                pass
                    if content_ok:
                        break
                except:
                    continue

            # 若在 iframe 找不到，直接在主頁找一個 contenteditable 區塊
            if not content_ok:
                try:
                    await page.fill('[contenteditable="true"]', content, timeout=2_000)
                    content_ok = True
                except:
                    pass

            if not content_ok:
                # 落到最保底：找 textarea
                try:
                    await page.fill("textarea", content, timeout=2_000)
                    content_ok = True
                except:
                    pass

            if not content_ok:
                raise RuntimeError("找不到可用的內文輸入區（content editor）")

            # 3) 發佈（或草稿）
            published = False
            # 先嘗試「發表」
            for sel in PUBLISH_BUTTON_CANDIDATES:
                try:
                    await page.click(sel, timeout=3_000)
                    published = True
                    break
                except:
                    pass

            # 如果發表按鈕沒點到就先儲存草稿，避免資料流失
            if not published:
                for sel in SAVE_DRAFT_BUTTONS:
                    try:
                        await page.click(sel, timeout=2_000)
                        break
                    except:
                        pass

            try:
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except PWTimeout:
                pass

            current_url = page.url

            return {
                "狀態": "成功",
                "結果": {
                    "帳號": "確定",
                    "keyword": keyword,
                    "title": title,
                    "url": current_url,
                },
                "note": "若後台按鈕文案/版型更動，請調整 selector 即可。",
            }

        except Exception as e:
            return {
                "狀態": "失敗",
                "步驟": "exception",
                "error": str(e),
            }
        finally:
            await context.close()
            await browser.close()
