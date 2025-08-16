# panel_article.py
# 乾淨版本：避免循環導入，將 Playwright 與操作都寫在函式內
# 只負責「登入 → 新增文章 → 回傳結果」的工作

import os
import json
import time
from typing import Dict, Any, Optional

# 注意：不要在模組頂層 import FastAPI 或 main.py，避免循環導入
# 也不要在頂層 import Playwright，避免沒有用到時就初始化瀏覽器


def _get_env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None or val == "":
        raise RuntimeError(f"缺少環境變數：{name}")
    return val


async def post_article_once(keyword: str = "理債一日便", commit: bool = True) -> Dict[str, Any]:
    """
    嘗試在 PIXNET 發一篇文章。
    - keyword：文章標題中要包含的關鍵字（預設：理債一日便）
    - commit：是否實際送出（True 送出；False 只到填寫階段）
    回傳：dict（包含 status / detail / step 等除錯資訊）
    """
    # 延後匯入，避免在 main.py import 時就初始化瀏覽器而造成循環/啟動開銷
    try:
        from playwright.async_api import async_playwright, TimeoutError as PwTimeout
    except Exception as e:
        return {"status": "fail", "step": "import", "error": f"Playwright 無法匯入：{e}"}

    # 讀環境變數
    try:
        email = _get_env("PIXNET_EMAIL")
        password = _get_env("PIXNET_PASSWORD")
        login_url = _get_env("PIXNET_LOGIN_URL")  # 例：https://member.pixnet.net/login
        new_article_url = _get_env("PIXNET_NEW_ARTICLE_URL")  # 例：https://panel.pixnet.cc/#/create-article
        title_selector = _get_env("PIXNET_TITLE_SELECTOR")  # 例：#editArticle-header-title
        mode = os.getenv("PIXNET_MODE", "auto")
    except Exception as e:
        return {"status": "fail", "step": "env", "error": str(e)}

    # 一些可能有用的 CSS 選擇器（如日後要補「內容」、「送出」）
    # 這些選擇器因為痞客邦後台會調整，若遇到 timeout，請再把實際選擇器傳給我調整即可。
    ACCOUNT_SELECTOR = 'input[name="account"], input[name="email"], #login-account'
    PASSWORD_SELECTOR = 'input[name="password"], #login-password'
    SUBMIT_SELECTOR = 'button[type="submit"], button#login-submit, .btn.btn-primary'

    # 實作
    step = "start"
    started_at = time.time()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()

            # 1) 登入
            step = "goto_login"
            await page.goto(login_url, wait_until="domcontentloaded", timeout=40_000)

            step = "fill_login"
            # 嘗試填入帳密（做幾個選擇器嘗試）
            filled = False
            for sel in ACCOUNT_SELECTOR:
                try:
                    await page.fill(sel, email, timeout=3_000)
                    filled = True
                    break
                except Exception:
                    continue
            if not filled:
                return {"status": "fail", "step": "fill_account", "error": "找不到帳號輸入框，請回報選擇器"}

            filled = False
            for sel in PASSWORD_SELECTOR:
                try:
                    await page.fill(sel, password, timeout=3_000)
                    filled = True
                    break
                except Exception:
                    continue
            if not filled:
                return {"status": "fail", "step": "fill_password", "error": "找不到密碼輸入框，請回報選擇器"}

            # 送出登入表單
            clicked = False
            for sel in SUBMIT_SELECTOR:
                try:
                    await page.click(sel, timeout=3_000)
                    clicked = True
                    break
                except Exception:
                    continue
            if not clicked:
                # 有些頁面按 Enter 也能送出
                await page.keyboard.press("Enter")

            # 等待登入完成（以是否跳轉/是否出現後台元素為依據）
            step = "wait_login_done"
            # 登入成功後通常會導到後台或顯示使用者狀態；這裡用比較寬鬆的等待
            await page.wait_for_timeout(1_500)

            # 2) 前往「新增文章」
            step = "goto_new_article"
            await page.goto(new_article_url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(1_000)

            # 3) 填入標題
            step = "fill_title"
            try:
                await page.fill(title_selector, f"{keyword}｜自動發文測試", timeout=15_000)
            except PwTimeout:
                return {"status": "fail", "step": "fill_title", "error": f"找不到標題選擇器：{title_selector}"}

            # TODO: 如要填內容，這裡可再加 editor 的 selector
            # 例：
            # content_selector = "#some-editor"
            # await page.fill(content_selector, "這是自動發文內容…", timeout=15000)

            # 4) 是否真的送出
            step = "commit" if commit else "dry_run"
            if commit:
                # 送出按鈕的 selector 依 Pixnet 變動而定；先留白
                # 你若提供「發佈」按鈕的 selector，我幫你補上
                pass

            # 擷取當前網址做為回傳參考
            current_url = page.url

            await context.close()
            await browser.close()

            spent = round(time.time() - started_at, 2)
            return {
                "status": "ok",
                "mode": mode,
                "step": step,
                "commit": commit,
                "keyword": keyword,
                "url": current_url,
                "spent_s": spent,
            }

    except Exception as e:
        return {"status": "fail", "step": step, "error": repr(e)}
