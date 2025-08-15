# panel_article.py
import os
from typing import List, Optional
from playwright.async_api import Page, Locator

# ===== 小工具：判斷元素可見 =====
async def _is_visible(el: Locator) -> bool:
    try:
        return await el.is_visible()
    except Exception:
        return False

# ===== 標題輸入框（多重 selector + 環境變數可覆蓋）=====
async def fill_title_with_fallbacks(page: Page, keyword: str) -> None:
    """
    多重 selector 尋找標題輸入框，找不到就 raise RuntimeError。
    可用環境變數 PIXNET_TITLE_SELECTOR 直接指定 selector（優先）。
    """
    title_text = f"{keyword}－自動發文測試"

    # 1) 允許從 Render 環境變數覆蓋 selector（優先）
    manual_sel = os.getenv("PIXNET_TITLE_SELECTOR", "").strip()
    if manual_sel:
        try:
            el = await page.wait_for_selector(manual_sel, state="visible", timeout=4000)
            await el.fill(title_text)
            return
        except Exception:
            pass  # 手動 selector 失敗就走備援

    # 2) 等候網路空閒（避免 DOM 尚未掛載）
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    # 3) 多組 CSS 備援（新 → 舊）
    css_selectors: List[str] = [
        "#editArticle-header-title",                 # 你找到的最新 ID
        'input[placeholder="請輸入文章標題"]',          # 常見 placeholder
        'input[name="title"]',
        'input[type="text"].title',                  # 舊版 class
        "input#title", "input#Title",
    ]

    # 4) 也嘗試用 Playwright 的「by_xxx」API 以 label/placeholder/role 尋找
    locator_candidates: List[Locator] = [
        page.get_by_placeholder("請輸入文章標題"),
        page.get_by_placeholder("標題"),
        page.get_by_role("textbox", name="標題"),
        page.get_by_label("標題", exact=False),
    ]

    # 先跑 locator 再跑 CSS，哪個先命中就用哪個
    for loc in locator_candidates:
        try:
            el = await loc.wait_for(state="visible", timeout=1500)
            if await _is_visible(el):
                await el.fill(title_text)
                return
        except Exception:
            continue

    for sel in css_selectors:
        try:
            el = await page.wait_for_selector(sel, state="visible", timeout=1500)
            if el and await _is_visible(el):
                await el.fill(title_text)
                return
        except Exception:
            continue

    raise RuntimeError("找不到標題輸入框（編輯頁面 DOM 可能改版）")

# ===== 內容輸入（支援 CKEditor iframe 或 contenteditable DIV）=====
async def fill_ckeditor_in_iframe_or_div(page: Page, html: str) -> bool:
    """
    嘗試以多重方式把 HTML 內容寫入：
      1) 先偵測 CKEditor 的 iframe（常見 class/ID/特徵），透過 frame 中的 editable 區塊 set innerHTML
      2) 再試編輯器的 contenteditable DIV（多個 selector）
    任何一種成功就回傳 True；全部失敗回傳 False（外層自行回報錯誤）
    """

    # 1) 先找常見 CKEditor iframe（class/ID 名稱會變，這裡放較寬鬆的特徵）
    iframe_sels = [
        'iframe.cke_wysiwyg_frame',
        'iframe[title*="編輯器"]',
        'iframe[title*="Rich Text"]',
        'iframe[title*="WYSIWYG"]',
    ]
    for sel in iframe_sels:
        try:
            frame = page.frame_locator(sel)
            # 確認 iframe 已 attach
            await frame.locator("body").wait_for(state="attached", timeout=3000)
            # 直接以 JS 注入 innerHTML（保留格式）
            await frame.evaluate(
                """(el, html)=>{ el.innerHTML = html; }""",
                await frame.locator("body").element_handle(),
                html,
            )
            return True
        except Exception:
            continue

    # 2) 不一定有 iframe；試試 contenteditable DIV
    div_sels = [
        '[contenteditable="true"]',
        '.ck-content[contenteditable="true"]',
        '#article-content, #content, .article-content',
    ]
    for sel in div_sels:
        try:
            target = await page.wait_for_selector(sel, state="visible", timeout=3000)
            # 若 editor 有 shadow DOM/虛擬 DOM，直接 .fill 可能不生效，所以改為 evaluate 寫 innerHTML
            await page.evaluate(
                """(el, html)=>{ el.innerHTML = html; }""",
                target,
                html,
            )
            return True
        except Exception:
            continue

    return False

# ===== 你的主流程（只示範填標題與內容的地方）=====
async def post_article_once(page: Page, keyword: str, commit: bool) -> dict:
    """
    回傳 dict：{"status": "ok"/"fail", "title": "...", "error": "..."}
    這個函式應該被你的 FastAPI 路由呼叫。
    這裡假設你已經登入並開啟「發文編輯頁」。
    """
    title = f"{keyword}－自動發文測試"

    # 1) 先填標題（多重 selector）
    try:
        await fill_title_with_fallbacks(page, keyword)
    except Exception as e:
        return {
            "status": "fail",
            "mode": "POST_REAL",
            "title": title,
            "error": f"標題錯誤：{e}",
        }

    # 2) 準備內文（你原本怎麼生 HTML 就怎麼產；這裡放示範用）
    #    也可以從環境變數或你的產文邏輯取得。
    content_html = f"""
    <h2>{keyword}</h2>
    <p>這是自動發文測試內容（HTML 保留）。</p>
    """

    # 3) 寫入內容（支援 CKEditor iframe 或 contenteditable DIV）
    ok = await fill_ckeditor_in_iframe_or_div(page, content_html)
    if not ok:
        return {
            "status": "fail",
            "mode": "POST_REAL",
            "title": title,
            "error": "內容錯誤：找不到可編輯的內文輸入區（編輯器可能改版）",
        }

    # 4) commit=True 才點「發布」（以下 selector 視你的頁面自行調整）
    if commit:
        publish_selectors = [
            'button:has-text("發布")',
            'button.publish',
            '#publishBtn',
        ]
        clicked = False
        for sel in publish_selectors:
            try:
                btn = await page.wait_for_selector(sel, state="visible", timeout=2000)
                await btn.click()
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            return {
                "status": "fail",
                "mode": "POST_REAL",
                "title": title,
                "error": "找不到『發布』按鈕（請更新 publish selector）",
            }

    return {"status": "ok", "mode": "POST_REAL", "title": title}
