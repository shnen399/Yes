import os
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright

app = FastAPI(title="PIXNET 自動發文系統")

PIXNET_EMAIL = os.getenv("PIXNET_EMAIL")
PIXNET_PASSWORD = os.getenv("PIXNET_PASSWORD")
PIXNET_LOGIN_URL = os.getenv("PIXNET_LOGIN_URL", "https://member.pixnet.net/login")
PIXNET_NEW_ARTICLE_URL = os.getenv("PIXNET_NEW_ARTICLE_URL", "https://panel.pixnet.cc/#/create-article")

@app.get("/")
def root():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.post("/post_article")
async def post_article(keyword: str = "理債一日便"):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 打開登入頁
            await page.goto(PIXNET_LOGIN_URL)

            # ✅ 改用新版 selector
            await page.fill('input[name="account"]', PIXNET_EMAIL)
            await page.fill('input[name="password"]', PIXNET_PASSWORD)
            await page.click('button[type="submit"]')

            # 等待登入完成（檢查是否跳轉）
            await page.wait_for_timeout(5000)

            # 開啟發文頁
            await page.goto(PIXNET_NEW_ARTICLE_URL)
            await page.wait_for_timeout(3000)

            # 找到標題欄位
            await page.fill('input[placeholder="請輸入文章標題"]', f"{keyword} 測試文章")
            await page.fill('div.ql-editor', f"這是一篇自動發文測試文章，關鍵字：{keyword}")

            # 點擊發佈按鈕
            await page.click('button:has-text("發佈")')
            await page.wait_for_timeout(5000)

            await browser.close()

            return JSONResponse({
                "狀態": "成功",
                "keyword": keyword,
                "note": "文章已嘗試發佈"
            })

    except Exception as e:
        return JSONResponse({
            "狀態": "失敗",
            "步驟": "exception",
            "error": f"{str(e)}\n{traceback.format_exc()}"
        })
