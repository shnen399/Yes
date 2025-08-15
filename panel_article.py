# panel_article.py
import asyncio
from typing import List, Dict, Tuple, Optional
from playwright.async_api import async_playwright, Page

# ===== 共用小工具 =====
async def _query_first_visible(page: Page, selectors: List[str], timeout: int = 8000):
    """
    依序嘗試多個 selector，回傳第一個可見的 Locator。
    """
    for sel in selectors:
        try:
            loc = page.locator(sel)
            await loc.first.wait_for(state="visible", timeout=timeout)
            return loc.first
        except Exception:
            continue
    return None

async def _fill_ckeditor_in_iframe(page: Page, html: str) -> bool:
    """
    在常見的 CKEditor iframe 內，將內容以 innerHTML 寫入。
    """
    iframe_sels = [
        'iframe.cke_wysiwyg_frame',
        'iframe[title="富文本編輯器"]',
        'iframe[title*="編輯器"]',
        'iframe[title*="Rich Text"]',
        'iframe[title*="WYSIWYG"]',
    ]
    # 找到可用的 iframe
    for sel in iframe_sels:
        try:
            frame_locator = page.frame_locator(sel)
            # 等待 body attach
            await frame_locator.locator("body").wait_for(state="attached", timeout=6000)
            # 寫 innerHTML
            await frame_locator.evaluate(
                """(html) => { document.body.innerHTML = html; }""",
                html,
            )
            return True
        except Exception:
            continue
    # 也試試非 iframe（有些新版用可編輯 div）
    try:
        content_div = await _query_first_visible(
            page,
            [
                '[contenteditable="true"]',
                '.cke_wysiwyg_div',
                '#article-content, #content, .article-content',
            ],
            timeout=3000,
        )
        if content_div:
            await content_div.click()
            await content_div.fill("")              # 先清空
            await content_div.evaluate(
                """(el, html) => { el.innerHTML = html; }""",
                html,
            )
            return True
    except Exception:
        pass
    return False

# ===== 主要流程 =====
async def post_article_once(
    *,
    cookies: List[Dict],
    title: str,
    content: str,
    commit: bool = True,
) -> Tuple[bool, str]:
    """
    真的登入 panel.pixnet.cc 發一篇文章。
    參數
      - cookies: 由 main.py 轉好的 cookies（含 .pixnet.cc / panel.pixnet.cc）
      - title:   文章標題
      - content: 文章 HTML 內容
      - commit:  True=按發佈；False=存草稿
    回傳 (ok, url_or_msg)
    """
    title_selectors = [
        '#editArticle-header-title',           # 你剛找到的新 ID（優先）
        'input[name="title"]',
        '#title, input#title',
        'input#article_title',
        'input[placeholder*="標題"]',
    ]
    save_buttons = [
        'button:has-text("儲存草稿")',
        'button:has-text("儲存")',
        '[data-qa="save-draft"]',
        '#save, #draft',
    ]
    publish_buttons = [
        'button:has-text("發佈")',
        '[data-qa="publish"]',
        '#publish, #post, .btn-primary:has-text("發佈")',
    ]

    # 依你原本站點流程調整：這裡用 panel.pixnet.cc 的發文頁（路徑依實際頁面為準）
    new_article_url = "https://panel.pixnet.cc/blog/articles/new"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context()
        # 載入 cookies
        if cookies:
            await context.add_cookies(cookies)

        page = await context.new_page()
        try:
            # 進入發文頁
            await page.goto(new_article_url, wait_until="domcontentloaded", timeout=30000)

            # 等待頁面主要區域載入（可視情況放更準確的容器 selector）
            await page.wait_for_load_state("networkidle", timeout=20000)

            # --- 填標題 ---
            title_input = await _query_first_visible(page, title_selectors, timeout=8000)
            if not title_input:
                return False, "找不到標題輸入框（頁面版面可能改了）"
            await title_input.fill("")  # 先清空
            await title_input.type(title)

            # --- 填內容（CKEditor / contenteditable）---
            ok = await _fill_ckeditor_in_iframe(page, content)
            if not ok:
                return False, "找不到內容編輯器（iframe 或可編輯區）"

            # --- 發佈或儲存 ---
            if commit:
                btn = await _query_first_visible(page, publish_buttons, timeout=4000)
                if not btn:
                    return False, "找不到『發佈』按鈕"
                await btn.click()
            else:
                btn = await _query_first_visible(page, save_buttons, timeout=4000)
                if not btn:
                    return False, "找不到『儲存草稿』按鈕"
                await btn.click()

            # 等待跳轉或成功訊息（視站點實作而定）
            await page.wait_for_load_state("networkidle", timeout=20000)

            # 嘗試抓發文後的文章網址（依實站回饋調整）
            # 例如成功後可能導向 /blog/articles/<id>/edit 或 /blog/post/<id>
            # 這裡先用目前頁面的 URL 回傳
            current_url = page.url
            return True, current_url

        except Exception as e:
            return False, f"post_article_once 例外：{e}"
        finally:
            await context.close()
            await browser.close()
