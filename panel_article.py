import os
from typing import List, Optional
from playwright.async_api import Page, Locator

# 小工具：判斷元素是否可見
async def _is_visible(el: Locator) -> bool:
    try:
        return await el.is_visible()
    except Exception:
        return False

async def fill_title_with_fallbacks(page: Page, keyword: str) -> None:
    """
    盡可能找到『標題』輸入框，找不到就拍圖＋存 HTML 方便除錯。
    也支援以環境變數 PIXNET_TITLE_SELECTOR 手動指定 selector。
    """
    title_text = f"{keyword}－自動發文測試"

    # --- 0) 若你在 Render 環境變數設定了自訂 selector，優先採用 ---
    manual_sel = os.getenv("PIXNET_TITLE_SELECTOR", "").strip()
    if manual_sel:
        try:
            el = await page.wait_for_selector(manual_sel, state="visible", timeout=4000)
            await el.fill(title_text)
            return
        except Exception:
            # 手動 selector 失敗就繼續用自動偵測
            pass

    # --- 1) 等到頁面比較穩定 ---
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    # --- 2) 直接命名/placeholder/ID/類別的常見 selector（新→舊） ---
    css_selectors: List[str] = [
        "#editArticle-header-title",                 # 你回報的最新 ID
        'input[placeholder="請輸入文章標題"]',
        'input[placeholder*="標題"]',
        'input[name="title"]',
        'input[id*="title"]',
        'input[type="text"].title',
        'input.title',
        'input[type="text"]',
    ]

    # Playwright 的高階查找（label/placeholder/role）
    locator_candidates: List[Locator] = [
        page.get_by_placeholder("請輸入文章標題"),
        page.get_by_placeholder("標題"),
        page.get_by_role("textbox", name="標題"),
        page.get_by_label("標題", exact=False),
    ]

    # --- 2a) 先跑高階查找 ---
    for loc in locator_candidates:
        try:
            await loc.wait_for(state="visible", timeout=1500)
            if await _is_visible(loc):
                await loc.fill(title_text)
                return
        except Exception:
            continue

    # --- 2b) 再跑 CSS 列表 ---
    for sel in css_selectors:
        try:
            el = await page.wait_for_selector(sel, state="visible", timeout=1500)
            if el and await _is_visible(el):
                await el.fill(title_text)
                return
        except Exception:
            continue

    # --- 3) 還是沒中：做「廣域偵測」找看起來像標題的 input ---
    try:
        # 找第一個可見的「文字 input」，通常在上方（標題）而不是內文
        inputs = page.locator('input[type="text"], input:not([type])')
        count = await inputs.count()
        for i in range(min(count, 8)):  # 前幾個就好
            el = inputs.nth(i)
            if await _is_visible(el):
                ph = (await el.get_attribute("placeholder")) or ""
                nm = (await el.get_attribute("name")) or ""
                _id = (await el.get_attribute("id")) or ""
                cls = (await el.get_attribute("class")) or ""
                if any(k in (ph+nm+_id+cls) for k in ["標題", "title", "Title"]):
                    await el.fill(title_text)
                    return
        # 若沒有關鍵字，就直接對第一個可見的 text input 試填
        for i in range(min(count, 5)):
            el = inputs.nth(i)
            if await _is_visible(el):
                await el.fill(title_text)
                return
    except Exception:
        pass

    # --- 4) 仍失敗：截圖 + 存 HTML 方便對位 ---
    debug_dir = "/tmp/pixnet_debug"
    os.makedirs(debug_dir, exist_ok=True)
    png_path  = os.path.join(debug_dir, "title_not_found.png")
    html_path = os.path.join(debug_dir, "title_page.html")
    try:
        await page.screenshot(path=png_path, full_page=True)
    except Exception:
        png_path = "(screenshot failed)"
    try:
        html = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        html_path = "(html save failed)"

    raise RuntimeError(
        f"找不到標題輸入框。已輸出除錯檔：screenshot={png_path}  html={html_path}\n"
        "你也可在 Render 環境變數新增 PIXNET_TITLE_SELECTOR=『你的 CSS 選擇器』先保險啟用。"
    )
