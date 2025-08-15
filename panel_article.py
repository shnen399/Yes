# panel_article.py
import asyncio
from typing import List, Dict, Tuple, Optional
from playwright.async_api import async_playwright, Page


async def _fill_ckeditor_in_iframe(page: Page, html: str) -> None:
    # PIXNET 後台是 CKEditor，會在 iframe 裡，這段會耐心找 iframe 並輸入內容
    iframe = await page.frame_locator("iframe.cke_wysiwyg_frame").first.frame()
    await iframe.wait_for_selector("body", state="attached")
    await iframe.evaluate(
        """(html) => {
            const body = document.querySelector('body');
            body.innerHTML = html;
        }""",
        html,
    )


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
      - cookies: 由 main.py 轉好的 cookies (含 .pixnet.cc / panel.pixnet.cc)
      - title: 文章標題
      - content: 文章 HTML 內容
      - commit: True=按發佈；False=存草稿
    回傳 (ok, url_or_msg)
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = await browser.new_context()
        if cookies:
            await ctx.add_cookies(cookies)

        page = await ctx.new_page()

        # 進後台（有 cookie 就會是登入狀態）
        await page.goto("https://panel.pixnet.cc/", wait_until="domcontentloaded")

        # 直接進「新增文章（圖文編輯器）」頁
        # 備用路徑（兩個都會試）：create?type=rich / articles/create
        target_urls = [
            "https://panel.pixnet.cc/blog/articles/create?type=rich",
            "https://panel.pixnet.cc/blog/articles/create",
        ]
        opened = False
        for u in target_urls:
            try:
                await page.goto(u, wait_until="domcontentloaded")
                opened = True
                break
            except Exception:
                pass
        if not opened:
            await browser.close()
            return False, "打不開發文頁面（可能 cookie 無效）"

        # 等標題輸入框
        # 常見 selector：input[name="title"] 或 #title
        title_sel_candidates = ['input[name="title"]', '#title', 'input#article_title']
        title_found = None
        for sel in title_sel_candidates:
            try:
                await page.wait_for_selector(sel, timeout=10000)
                title_found = sel
                break
            except Exception:
                pass
        if not title_found:
            await browser.close()
            return False, "找不到標題輸入框（頁面版面可能改了）"

        # 填標題
        await page.fill(title_found, title)

        # 填 CKEditor 內文（在 iframe）
        try:
            await _fill_ckeditor_in_iframe(page, content)
        except Exception:
            await browser.close()
            return False, "填入內容失敗（CKEditor/iframe 可能改版）"

        # 發佈或存草稿
        # 發佈按鈕常見：button:has-text("發表") / ("發表公開文章")
        publish_selectors = [
            'button:has-text("發表公開文章")',
            'button:has-text("發表")',
            'text=發表公開文章',
            'text=發表',
        ]
        draft_selectors = [
            'button:has-text("存為草稿")',
            'text=存為草稿',
        ]

        clicked = False
        if commit:
            for sel in publish_selectors:
                try:
                    await page.click(sel, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    pass
        else:
            for sel in draft_selectors:
                try:
                    await page.click(sel, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    pass

        if not clicked:
            await browser.close()
            return False, "找不到發佈/草稿按鈕（頁面版面可能改了）"

        # 等發佈後跳轉（或提示）
        # 常見：會跳到文章清單或單篇頁，拿當前網址回傳
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        url = page.url
        await browser.close()
        return True, url
