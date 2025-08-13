from fastapi import FastAPI
from playwright.sync_api import sync_playwright

app = FastAPI(title="PIXNET 自動海報", version="0.1.0")

@app.get("/")
def root():
    return {"ok": True, "msg": "service alive"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/post_article")
def post_article():
    # 確認瀏覽器可用：打開 example.com 並回傳標題
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com", timeout=60_000)
        title = page.title()
        browser.close()
    return {"status": "success", "title": title}
