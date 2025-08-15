import asyncio
import os
import random
import time
from playwright.async_api import async_playwright

# 發文函數
async def post_article_once():
    accounts = os.getenv("PIXNET_ACCOUNTS", "").strip().splitlines()
    if not accounts:
        return {"status": "fail", "error": "沒有設定 PIXNET 帳號"}

    email, password = random.choice([a.split(":", 1) for a in accounts if ":" in a])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 登入
            await page.goto("https://panel.pixnet.cc/login")
            await page.fill('input[name="account"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)

            # 進入發文頁面
            await page.goto("https://panel.pixnet.cc/blog/articles/new")
            await page.wait_for_timeout(3000)

            # 標題欄位 selector
            title_sel_candidates = [
                '#editArticle-header-title',  # 你提供的最新 ID
                'input[name="title"]',
                '#title',
                'input#article_title'
            ]
            title_filled = False
            for sel in title_sel_candidates:
                try:
                    await page.fill(sel, f"自動發文測試 {time.time()}")
                    title_filled = True
                    break
                except:
                    continue
            if not title_filled:
                return {"status": "fail", "error": "找不到標題欄位"}

            # 內文欄位 selector
            body_selectors = [
                "textarea[name='body']",
                "textarea#body",
                "div[contenteditable='true']",
                ".ck-content[contenteditable='true']",
                "#editArticle-body"
            ]
            body_filled = False
            for sel in body_selectors:
                try:
                    await page.fill(sel, "這是一篇自動發文的測試內文。")
                    body_filled = True
                    break
                except:
                    continue
            if not body_filled:
                return {"status": "fail", "error": "找不到內文欄位"}

            # 儲存文章
            await page.click('button:has-text("發佈")')
            await page.wait_for_timeout(3000)

            await browser.close()
            return {"status": "success", "message": f"帳號 {email} 發文成功"}

        except Exception as e:
            await browser.close()
            return {"status": "fail", "error": str(e)}

# 測試執行
if __name__ == "__main__":
    asyncio.run(post_article_once())
