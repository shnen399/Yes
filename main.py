import os
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

# --- Playwright ---
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

app = FastAPI(title="PIXNET 自動發文系統 + 測試頁面", version="0.1.1")

# 讀 env
PIXNET_EMAIL = os.getenv("PIXNET_EMAIL", "")
PIXNET_PASSWORD = os.getenv("PIXNET_PASSWORD", "")
PIXNET_LOGIN_URL = os.getenv("PIXNET_LOGIN_URL", "https://member.pixnet.net/login")
PIXNET_NEW_ARTICLE_URL = os.getenv("PIXNET_NEW_ARTICLE_URL", "https://panel.pixnet.cc/")
PIXNET_TITLE_SELECTOR = os.getenv("PIXNET_TITLE_SELECTOR", 'input[placeholder="請輸入文章標題"]')

def ok(data):
    return {"狀態": "成功", "結果": data}

def fail(step, msg):
    return {"狀態": "失敗", "步驟": step, "error": msg}

async def try_fill(page, selectors: List[str], value: str, step_name: str, timeout=6000):
    last_err = None
    for css in selectors:
        try:
            await page.wait_for_selector(css, state="visible", timeout=timeout)
            await page.fill(css, value)
            return css
        except Exception as e:
            last_err = e
    raise RuntimeError(f"{step_name}：找不到可用 selector，最後錯誤：{last_err}")

async def try_click(page, selectors: List[str], step_name: str, timeout=6000):
    last_err = None
    for css in selectors:
        try:
            # 支援 "text=..." 與 CSS
            if css.startswith("text="):
                await page.get_by_text(css.replace("text=",""), exact=True).click(timeout=timeout)
            else:
                await page.wait_for_selector(css, state="visible", timeout=timeout)
                await page.click(css)
            return css
        except Exception as e:
            last_err = e
    raise RuntimeError(f"{step_name}：點擊不到按鈕，最後錯誤：{last_err}")

async def do_pixnet_post(keyword: str):
    # 發文內容（示範可先用 keyword 當標題；內容放一些測試字串）
    title_text = f"[自動發文 - 測試] {keyword}"
    content_text = f"這是自動化測試文章，關鍵字：{keyword}\n（由 Render + FastAPI + Playwright 發表）"

    # 安全檢查
    if not PIXNET_EMAIL or not PIXNET_PASSWORD:
        return fail("env", "缺少 PIXNET_EMAIL / PIXNET_PASSWORD")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(locale="zh-TW")
        page = await context.new_page()

        try:
            # 1) 登入
            await page.goto(PIXNET_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)

            # 常見帳號/密碼欄位 selector（多路徑嘗試）
            email_selectors = [
                'input[name="email"]',
                '#email',
                '#input-account',
                'input[type="email"]',
            ]
            pwd_selectors = [
                'input[name="password"]',
                '#password',
                '#input-password',
                'input[type="password"]',
            ]
            await try_fill(page, email_selectors, PIXNET_EMAIL, "填入帳號")
            await try_fill(page, pwd_selectors, PIXNET_PASSWORD, "填入密碼")

            # 按登入（多路徑）
            login_btns = [
                'button[type="submit"]',
                'button#login-button',
                'button:has-text("登入")',
                'text=登入',
            ]
            await try_click(page, login_btns, "點擊登入")

            # 等登入完成（看是否導回後台 / 或登入成功狀態）
            # 這裡保守等待一小段時間以通過各種跳轉
            await page.wait_for_timeout(2000)

            # 2) 進入「新增文章」頁
            await page.goto(PIXNET_NEW_ARTICLE_URL, wait_until="domcontentloaded", timeout=45000)

            # 等標題欄（用你設定的 PIXNET_TITLE_SELECTOR）
            await page.wait_for_selector(PIXNET_TITLE_SELECTOR, state="visible", timeout=15000)
            await page.fill(PIXNET_TITLE_SELECTOR, title_text)

            # 3) 內容欄位（嘗試幾種內容區）
            #   - 面板常用可編輯區： [contenteditable="true"]
            #   - 一些編輯器在 iframe 內，需要切到 iframe；我們先嘗試常見可編輯區
            content_selectors = [
                '[contenteditable="true"]',
                'div.note-editable',
                'div[role="textbox"]',
                'textarea[name="content"]',
                'textarea#post_content',
            ]

            filled = False
            for css in content_selectors:
                try:
                    await page.wait_for_selector(css, state="visible", timeout=4000)
                    await page.fill(css, content_text)
                    filled = True
                    break
                except Exception:
                    continue

            # 如果一般方式失敗，嘗試在頁面上直接執行 JS（將第一個 contenteditable 寫入）
            if not filled:
                await page.evaluate(
                    """(txt) => {
                        const el = document.querySelector('[contenteditable="true"], div.note-editable, div[role="textbox"]');
                        if (el) {
                            el.focus();
                            const sel = window.getSelection();
                            sel.removeAllRanges();
                            el.innerText = txt;
                            return true;
                        }
                        return false;
                    }""",
                    content_text,
                )

            # 4) 按「發表公開文章」或同義按鈕（多路徑）
            publish_btns = [
                'button:has-text("發表公開文章")',
                'button:has-text("發表文章")',
                'text=發表公開文章',
                'text=發表文章',
            ]
            await try_click(page, publish_btns, "點擊發表")

            # 5) 等待成功訊號（頁面跳轉或 toast）
            await page.wait_for_timeout(3000)

            # 嘗試抓發文後的 URL（如果成功通常會有文章頁）
            post_url = page.url

            return ok({
                "status": "ok",
                "title": title_text,
                "post_url": post_url
            })
        except PWTimeout as e:
            return fail("timeout", str(e))
        except Exception as e:
            return fail("exception", str(e))
        finally:
            await context.close()
            await browser.close()


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/test", response_class=HTMLResponse)
def test_page():
    # 方便手機一鍵測試
    html = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head><meta charset="UTF-8"><title>PIXNET 測試發文頁</title></head>
    <body>
      <h2>PIXNET 測試發文頁</h2>
      <button onclick="postArticle()">測試發文</button>
      <pre id="result">（點上面按鈕）</pre>
      <script>
        async function postArticle() {
          const box = document.getElementById('result');
          box.textContent = '發送中…';
          try {
            const res = await fetch('/post_article?keyword=' + encodeURIComponent('理債一日便'), { method: 'POST' });
            const data = await res.json();
            box.textContent = JSON.stringify(data, null, 2);
          } catch (e) {
            box.textContent = String(e);
          }
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/post_article")
async def post_article(keyword: Optional[str] = Query(default="理債一日便")):
    """
    真的自動登入 + 發文
    """
    result = await do_pixnet_post(keyword)
    return JSONResponse(result)
