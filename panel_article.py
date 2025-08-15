# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import asyncio
from playwright.async_api import Page

async def fill_title(page: Page, keyword: str):
    """
    尋找並填入 PIXNET 文章標題（多重 selector 備援）。
    找不到會自動截圖存檔，方便除錯。
    """
    title = f"{keyword}－自動發文測試"

    # 依序嘗試的 selector（由新到舊）
    title_selectors = [
        "#editArticle-header-title",               # 你提供的最新 ID
        'input[placeholder="請輸入文章標題"]',        # 常見 placeholder
        'input[name="title"]',
        'input[type="text"].title',                # 舊版 class
    ]

    # 等待網路靜止，避免 DOM 還沒掛好
    await page.wait_for_load_state("networkidle")

    matched_selector = None
    title_box = None
    for sel in title_selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=2000, state="visible")
            if el:
                matched_selector = sel
                title_box = el
                break
        except Exception:
            continue

    if not title_box:
        # 找不到就截圖，幫你看畫面長怎樣
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        shot = Path(f"/tmp/pixnet_title_not_found_{ts}.png")
        await page.screenshot(path=str(shot), full_page=True)
        raise RuntimeError(f"找不到標題輸入框（selector 可能又改了）。已截圖：{shot}")

    print(f"[debug] title matched selector: {matched_selector}")
    await title_box.fill(title)
