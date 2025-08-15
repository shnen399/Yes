import os
import json
import asyncio
from typing import List, Dict, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# ───── FastAPI 基本設定 ─────────────────────────────────────────────────────────
app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ───── 輔助：讀 cookies.json ─────────────────────────────────────────────────────
COOKIE_FILE = "cookies.json"

def load_cookies() -> List[Dict]:
    """
    讀取 cookies.json
    你的 cookies.json 格式（單一物件）：
    [
      {
        "PIXCCSESSION": "...",
        "PIXSID": "...",
        "XSRF-TOKEN": "...",
        "uid": "..."
      }
    ]
    """
    if not os.path.exists(COOKIE_FILE):
        return []
    try:
        data = json.load(open(COOKIE_FILE, "r", encoding="utf-8"))
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return []

# 轉成 Playwright 的 cookie 格式
def to_playwright_cookies(raw_cookie_obj: Dict) -> List[Dict]:
    """
    把 cookies.json 內的鍵值轉為 Playwright context.add_cookies 需要的格式。
    這裡同時塞入 pixnet.cc / panel.pixnet.cc / pixnet.net，提升命中率。
    """
    mapping = [
        ("PIXCCSESSION", ".pixnet.cc", "/"),
        ("PIXSID", ".pixnet.cc", "/"),
        ("XSRF-TOKEN", "panel.pixnet.cc", "/"),
        ("uid", "panel.pixnet.cc", "/"),
        # 若你之後加到 cookies.json，也可在這裡補：
        # ("webuserid", ".pixnet.net", "/"),
        # ("PIXNET_SOMETHING", ".pixnet.net", "/"),
    ]
    out = []
    for name, domain, path in mapping:
        val = raw_cookie_obj.get(name)
        if not val:
            continue
        out.append({
            "name": name,
            "value": val,
            "domain": domain,
            "path": path,
            "httpOnly": False,
            "secure": True if domain.endswith(".cc") or domain.endswith(".net") else False,
            "sameSite": "Lax",
        })
    return out

# ───── 產文：先做個安全可測試的範例（可自行換成抓新聞的邏輯） ─────────────────────────────
def build_article_from_keyword(keyword: str) -> Dict[str, str]:
    title = f"{keyword}｜自動摘要筆記（{asyncio.get_event_loop().time():.0f})"
    points = [
        f"【3 行看重點】關鍵字：{keyword}",
        "市場快訊：整理三則相關新聞 / 議題摘要（示意）",
        "投資提醒：本文僅示範，非投資建議",
    ]
    content = "\n".join(f"- {p}" for p in points) + "\n\n（這裡可以換成你真正的抓新聞與生成內容）"
    return {"title": title, "content": content}

# ───── Playwright 自動登入與發文（以 Cookie 登入）──────────────────────────────────
async def pixnet_post_with_cookies(title: str, content: str) -> (bool, str):
    """
    回傳 (ok, msg_or_url)
    ok=True 時 msg_or_url 會盡量帶上建立完成的後台網址（或提示）
    """
    from playwright.async_api import async_playwright

    all_cookie_objs = load_cookies()
    if not all_cookie_objs:
        return False, "找不到 cookies.json 或內容為空"

    cookies_for_pw = to_playwright_cookies(all_cookie_objs[0])
    if not cookies_for_pw:
        return False, "cookies.json 內容鍵值不足（至少需 PIXCCSESSION / PIXSID / XSRF-TOKEN / uid）"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = await browser.new_context(locale="zh-TW", viewport={"width": 1280, "height": 900})
        await context.add_cookies(cookies_for_pw)
        page = await context.new_page()

        # 1) 驗證是否已登入
        try:
            await page.goto("https://panel.pixnet.cc/", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            await context.close(); await browser.close()
            return False, f"無法開啟後台：{e}"

        # 嘗試找幾個常見元素（登入狀態的指標）：
        logged_in = False
        try:
            # 右上角頭像或使用者選單常見 class/文字（不同帳號版面可能不同；多路徑嘗試）
            if await page.locator("text=登出").first.is_visible():
                logged_in = True
        except:
            pass
        try:
            if await page.locator("a[href*='logout']").first.is_visible():
                logged_in = True
        except:
            pass
        try:
            # 若自動導到 dashboard 也算成功
            if "panel.pixnet.cc" in page.url:
                logged_in = True
        except:
            pass

        if not logged_in:
            await context.close(); await browser.close()
            return False, "疑似未登入：Cookie 可能過期或網頁版面不同，請重新擷取 cookies.json"

        # 2) 嘗試前往新增文章頁（不同帳號路徑可能不同，這裡提供幾個常見路徑）
        create_urls = [
            "https://panel.pixnet.cc/blog/articles/create",
            "https://panel.pixnet.cc/blog/articles/new",
            "https://panel.pixnet.cc/blog/articles",  # 有些會到列表，之後按「新增」
        ]
        goto_ok = False
        for u in create_urls:
            try:
                await page.goto(u, wait_until="domcontentloaded", timeout=45000)
                goto_ok = True
                break
            except:
                continue
        if not goto_ok:
            await context.close(); await browser.close()
            return False, "找不到新增文章頁（路徑可能變更，需要你提供實際新增文章的網址）"

        # 3) 嘗試填入標題與內容（不同編輯器有不同 selector，這裡提供多組 fallback）
        filled_title = False
        title_selectors = [
            "input[name='title']",
            "input#title",
            "input.ipt-title",
            "input[type='text'][placeholder*='標題']",
        ]
        for sel in title_selectors:
            try:
                if await page.locator(sel).first.is_visible():
                    await page.fill(sel, title)
                    filled_title = True
                    break
            except:
                pass
        if not filled_title:
            # 有些是 iframe 內的 title 欄位
            try:
                f = page.frame_locator("iframe")
                await f.locator("input[name='title']").fill(title)
                filled_title = True
            except:
                pass

        # 內容（有些為 iframe 內的 contenteditable）
        filled_body = False
        body_selectors = [
            "textarea[name='body']",
            "textarea#body",
            "div[contenteditable='true']",
            ".ck-content[contenteditable='true']",
        ]
        for sel in body_selectors:
            try:
                if await page.locator(sel).first.is_visible():
                    await page.fill(sel, content)
                    filled_body = True
                    break
            except:
                pass
        if not filled_body:
            # 常見：CKEditor 在 iframe 內
            try:
                f = page.frame_locator("iframe")
                await f.locator(".cke_wysiwyg_div, div[contenteditable='true']").fill(content)
                filled_body = True
            except:
                pass

        if not (filled_title and filled_body):
            await context.close(); await browser.close()
            return False, "未能找到標題或內文欄位（編輯器 selector 需微調）"

        # 4) 嘗試點擊發佈（常見按鈕文字/selector；若找不到就停在這一步）
        published = False
        publish_candidates = [
            "button:has-text('發佈')",
            "button:has-text('發布')",
            "button:has-text('公開')",
            "text=發表文章",
            "text=發布文章",
            "text=發佈文章",
        ]
        for sel in publish_candidates:
            try:
                el = page.locator(sel).first
                if await el.is_visible():
                    await el.click()
                    published = True
                    break
            except:
                pass

        # 有些頁面會先出現「儲存草稿」再「發佈」
        if not published:
            try:
                if await page.locator("text=儲存草稿").first.is_visible():
                    await page.click("text=儲存草稿")
                # 再找一次發佈
                for sel in publish_candidates:
                    try:
                        el = page.locator(sel).first
                        if await el.is_visible():
                            await el.click()
                            published = True
                            break
                    except:
                        pass
            except:
                pass

        current_url = page.url
        await context.close()
        await browser.close()

        if not published:
            return False, f"已填入標題與內文，但找不到『發佈』按鈕；目前停留頁面：{current_url}"
        return True, f"已嘗試發佈，請到後台確認。頁面：{current_url}"

# ───── API 定義 ────────────────────────────────────────────────────────────────
class PostReq(BaseModel):
    keyword: str
    commit: Optional[bool] = False

@app.get("/")
async def root():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.post("/post_article")
async def post_article(req: PostReq):
    # 產文（你可替換成抓 RSS + 摘要的真正邏輯）
    article = build_article_from_keyword(req.keyword)
    title, content = article["title"], article["content"]

    # 安全預覽模式（預設）
    allow_real = os.getenv("ALLOW_POST", "0") == "1"
    if not req.commit or not allow_real:
        mode = "PREVIEW_ONLY" if not req.commit else "ALLOW_POST_OFF"
        hint = "預覽模式，未發文" if mode == "PREVIEW_ONLY" else "環境變數 ALLOW_POST=1 才會真的發文"
        return {
            "status": "success",
            "mode": mode,
            "article": {"title": title, "content": content},
            "hint": hint,
        }

    # 真發文
    ok, msg = await pixnet_post_with_cookies(title, content)
    if ok:
        return {"status": "success", "mode": "POST_REAL", "title": title, "result": msg}
    else:
        return {"status": "fail", "mode": "POST_REAL", "title": title, "error": msg}

# ───── Render / 本地啟動 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
