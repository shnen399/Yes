def _split_accounts(raw: str):
    """
    解析多帳號字串：
    - 可用「換行」、「逗號」、「空白」分隔
    - 每組格式：email:password
    """
    if not raw:
        return []
    parts = []
    for seg in raw.replace("\r", "\n").replace(",", "\n").split("\n"):
        seg = seg.strip()
        if not seg:
            continue
        # 允許 "email:pass" 或 "email ： pass"（中英冒號都接）
        seg = seg.replace("：", ":")
        if ":" in seg:
            email, pwd = seg.split(":", 1)
            email, pwd = email.strip(), pwd.strip()
            if email and pwd:
                parts.append((email, pwd))
    return parts


async def _do_post_with_playwright(kw: str):
    """
    真的執行：登入 → 新增文章 → 填標題/內文 → 視模式發表（或停在草稿）
    回傳 dict 作為結果
    """
    login_url = env_or("PIXNET_LOGIN_URL", "https://member.pixnet.net/login")
    new_url   = env_or("PIXNET_NEW_ARTICLE_URL", "https://panel.pixnet.cc/")
    title_sel = env_or("PIXNET_TITLE_SELECTOR", 'input[name="title"]')
    # 你剛剛也有設定 PIXNET_CONTENT_SELECTOR，沒設就用常見的 .note-editable
    content_sel = env_or("PIXNET_CONTENT_SELECTOR", ".note-editable")
    mode     = (env_or("PIXNET_MODE", "auto") or "auto").lower()
    blog     = env_or("BLOG_HOST", "")
    accounts = _split_accounts(env_or("PIXNET_ACCOUNTS", ""))

    if not accounts:
        return {"ok": False, "step": "check_env", "error": "PIXNET_ACCOUNTS 未設定或格式錯誤（email:password）"}

    # 文章內容（示範）：你可以改成你要的模板
    content = f"<p>自動發文測試：{kw}</p><p>來源：{blog}</p>"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        used_acc = None
        try:
            # 嘗試逐一帳號登入
            for email, pwd in accounts:
                try:
                    await page.goto(login_url, timeout=60_000)
                    # 嘗試常見的登入欄位（可依實際頁面調整）
                    # 帳號
                    await page.fill('input[name="email"], input[name="username"], #email', email, timeout=20_000)
                    # 密碼
                    await page.fill('input[name="password"], #password', pwd, timeout=20_000)
                    # 送出
                    # 常見 submit 按鈕：button[type=submit] 或 文字包含「登入」
                    if await page.locator('button[type="submit"]').count():
                        await page.click('button[type="submit"]')
                    else:
                        # 後備：找文字
                        await page.get_by_role("button", name=lambda v: "登入" in v or "Login" in v).click(timeout=20_000)

                    # 等到登入完成（用是否跳到 panel 或者 cookie 判斷）
                    # 這裡用簡單等待：有登入後才會有的元素；若沒把握可改成等待 URL 變化或特定元素
                    await page.wait_for_timeout(1500)
                    # 進控制台（或直接新文章頁）
                    await page.goto(new_url, timeout=60_000)
                    used_acc = (email, pwd)
                    break
                except Exception:
                    # 下一組帳密再試
                    continue

            if not used_acc:
                return {"ok": False, "step": "login", "error": "所有帳號登入失敗"}

            # 可能需要點到「發表新文章」的頁面（不同後台 URL 會不同）
            # 若你的 new_url 已經是新文章頁，就會直接有 title 欄位可用
            # 若不是，可以視需要在這裡補「點選『新增文章』」的流程。

            # 填標題與內容
            await page.wait_for_selector(title_sel, timeout=30_000)
            await page.fill(title_sel, f"{kw}｜{os.getenv('ENV_TAG','')}".strip("｜"))

            # 內容編輯器（很多平台用 iframe + contentEditable）
            # 這裡先直接對常見的 .note-editable 填 HTML
            try:
                await page.wait_for_selector(content_sel, timeout=30_000)
                # 有些編輯器需要 focus 後插入
                await page.click(content_sel)
                await page.fill(content_sel, "")  # 清空
                # 使用 JS 設定 innerHTML，以保留簡單排版
                await page.evaluate(
                    """(sel, html) => {
                        const el = document.querySelector(sel);
                        if (el) { el.innerHTML = html; }
                    }""",
                    content_sel, content
                )
            except PWTimeoutError:
                # 如果你的編輯器在 iframe 內，這裡可以再補切換到 iframe 的流程
                pass

            # 發表 / 存草稿
            did_publish = False
            detail_msg = "已填寫標題與內容"
            try:
                if mode == "live":
                    # 嘗試幾種常見發表按鈕
                    publish_candidates = [
                        'button:has-text("發表")',
                        'button:has-text("發布")',
                        'button:has-text("發佈")',
                        'button:has-text("Publish")',
                        '[data-action="publish"]',
                    ]
                    for sel in publish_candidates:
                        if await page.locator(sel).count():
                            await page.click(sel)
                            did_publish = True
                            detail_msg = "已嘗試點擊發表按鈕"
                            break
                else:
                    # 非 live 模式，就別亂發；你也可改成按「儲存草稿」
                    detail_msg = "非 live 模式，僅示範填寫（未點擊發表）"
            except Exception as e:
                detail_msg = f"點擊發表時發生例外：{e}"

            # 等待一點時間，看是否導向成功頁或出現成功提示
            await page.wait_for_timeout(1200)

            return {
                "ok": True,
                "mode": mode,
                "did_publish": did_publish,
                "used_account": used_acc[0],
                "detail": detail_msg,
            }
        finally:
            await ctx.close()
            await browser.close()


@app.api_route("/post_article", methods=["GET", "POST"])
async def post_article(keyword: Optional[str] = Query(None), payload: Optional[dict] = Body(None)):
    # 同時支援 GET(Query) 與 POST(Body)
    kw = keyword
    if (not kw) and payload and isinstance(payload, dict):
        kw = payload.get("keyword")
    kw = kw or "理債一日便"

    try:
        result = await _do_post_with_playwright(kw)
        env_info = {
            "BLOG_HOST": env_or("BLOG_HOST"),
            "PIXNET_MODE": env_or("PIXNET_MODE", "auto"),
        }
        if result.get("ok"):
            return JSONResponse({
                "狀態": "成功",
                "結果": result,
                "env": env_info,
            })
        else:
            return JSONResponse({
                "狀態": "失敗",
                "結果": result,
                "env": env_info,
            }, status_code=500)
    except Exception as e:
        return JSONResponse({
            "狀態": "錯誤",
            "error": str(e),
            "env": {
                "BLOG_HOST": env_or("BLOG_HOST"),
                "PIXNET_MODE": env_or("PIXNET_MODE", "auto"),
            }
        }, status_code=500)
