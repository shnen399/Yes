# panel_article.py
import asyncio
from typing import List, Dict, Tuple
from playwright.async_api import async_playwright, Page

# ========= 小工具 =========
async def _query_first_visible(page: Page, selectors: List[str], timeout: int = 6000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None

async def _fill_ckeditor_in_iframe_or_div(page: Page, html: str) -> bool:
    # 先試常見 CKEditor iframe
    iframe_sels = [
        'iframe.cke_wysiwyg_frame',
        'iframe[title*="編輯器"]',
        'iframe[title*="Rich Text"]',
        'iframe[title*="WYSIWYG"]',
    ]
    for sel in iframe_sels:
        try:
            frame = page.frame_locator(sel)
            await frame.locator("body").wait_for(state="attached", timeout=5000)
            await frame.evaluate("""(html)=>{ document.body.innerHTML = html; }""", html)
            return True
        except Exception:
            continue
    # 再試可編輯區 div
    div_sels = [
        '[contenteditable="true"]',
        '.ck-content[contenteditable="true"]',
        '#article-content, #content, .article-content',
    ]
    target = await _query_first_visible(page, div_sels, timeout=3000)
    if target:
        # 用 evaluate 設 innerHTML，避免 .fill() 把標籤轉純文字
        await target.evaluate("""(el, html)=>{ el.innerHTML = html; }""", html)
        return True
    return False

# ========= 標題輸入框：多重 selector 備援 =========
async def fill_title_with_fallbacks(page: Page, keyword: str) -> None:
    """
    依序嘗試多組 selector 找到標題輸入框並填入。
    找不到就 raise RuntimeError。
    """
    title = f"{keyword}－自動發文測試"

    title_selectors = [
        "#editArticle-header-title",            # 你提供的最新 ID（優先）
        'input[placeholder="請輸入文章標題"]',     # 常見 placeholder
        'input[name="title"]',
        '#title, input#title',
        'input[type="text"].title',             # 舊版 class
        'input[aria-label*="標題"]',
    ]

    # 等頁面穩定
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    box = await _query_first_visible(page, title_selectors, timeout=2500)
    if not box:
        raise RuntimeError("找不到標題輸入框（編輯頁面可能改版）")

    await box.fill(title)

# ========= 主要發文流程 =========
async def post_article_once(
    *,
    cookies: List[Dict],
    title: str,
    content: str,
    commit: bool = True,
) -> Tuple[bool, str]:
    """
    使用已登入 cookies 直接開後台發文頁，填標題與內文後發佈/存草稿。
    參數
      - cookies: 由 main.py 轉換成 Playwright 需要格式的 cookies
      - title:   文章標題（若你想用 keyword 自動組，也可在呼叫前組好丟進來）
      - content: 文章 HTML 內容
      - commit:  True=發佈；False=存草稿
    回傳 (ok, url_or_msg)
    """
    new_article_url = "https://panel.pixnet.cc/blog/articles/new"
    publish_selectors = [
        'button:has-text("發佈")',
        '[data-qa="publish"]',
        '#publish, #post, .btn-primary:has-text("發佈")',
    ]
    draft_selectors = [
        'button:has-text("儲存草稿")',
        '[data-qa="save-draft"]',
        '#save, #draft',
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context()
        if cookies:
            await context.add_cookies(cookies)

        page = await context.new_page()
        try:
            # 進發文頁（有 cookie 就會是登入狀態）
            await page.goto(new_article_url, wait_until="domcontentloaded", timeout=30000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            # ---- 填標題（使用多重 selector）----
            # 若你想強制用參數 title，則把 fill_title_with_fallbacks 換成直接填入 title
            try:
                # 優先用你給的 selector；若要保留參數 title，直接填 title 即可
                title_selectors = [
                    "#editArticle-header-title",
                    'input[placeholder="請輸入文章標題"]',
                    'input[name="title"]',
                    '#title, input#title',
                    'input[type="text"].title',
                    'input[aria-label*="標題"]',
                ]
                box = await _query_first_visible(page, title_selectors, timeout=2500)
                if not box:
                    raise RuntimeError("找不到標題輸入框（編輯頁面可能改版）")
                await box.fill(title)
            except Exception as e:
                await context.close()
                await browser.close()
                return False, f"標題錯誤：{e}"

            # ---- 填內容（CKEditor 或可編輯區）----
            ok = await _fill_ckeditor_in_iframe_or_div(page, content)
            if not ok:
                await context.close()
                await browser.close()
                return False, "找不到內容編輯器（iframe 或可編輯 div）"

            # ---- 發佈或存草稿 ----
            if commit:
                btn = await _query_first_visible(page, publish_selectors, timeout=5000)
            else:
                btn = await _query_first_visible(page, draft_selectors, timeout=5000)

            if not btn:
                await context.close()
                await browser.close()
                return False, "找不到『發佈/儲存草稿』按鈕"

            await btn.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            url = page.url
            await context.close()
            await browser.close()
            return True, url

        except Exception as e:
            await context.close()
            await browser.close()
            return False, f"post_article_once 例外：{e}"
