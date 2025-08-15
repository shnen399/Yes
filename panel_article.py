# ---- 找並填入「標題」：多重 selector 備援 ----
title = f"{keyword}－自動發文測試"

title_selectors = [
    "#editArticle-header-title",           # 你提供的最新 ID
    'input[placeholder="請輸入文章標題"]',    # 常見 placeholder
    'input[name="title"]',
    'input[type="text"].title',            # 舊版 class
]

# 等候頁面載入穩定再找元素
await page.wait_for_load_state("networkidle")

title_box = None
for sel in title_selectors:
    try:
        # 有些頁面會延遲掛上 DOM，給它一點時間
        el = await page.wait_for_selector(sel, timeout=2000, state="visible")
        if el:
            title_box = el
            break
    except Exception:
        continue

if not title_box:
    raise RuntimeError("找不到標題輸入框（selector 可能又改了）")

await title_box.fill(title)
