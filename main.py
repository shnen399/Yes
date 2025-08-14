@app.post("/post_article")
async def post_article():
    accounts = _read_accounts_from_env()
    if not accounts:
        return {"status": "fail", "error": "未偵測到帳號資訊"}

    email, pwd = accounts[0]  # 先用第一個帳號測試

    # 測試文章內容
    title = "測試發文 - 系統驗證"
    content = """
    <p>這是一篇測試文章，用來確認 PIXNET 自動發文系統是否正常運作。</p>
    <p>測試時間：系統自動生成</p>
    """

    # 這裡呼叫真實發文模組
    try:
        # 直接呼叫你原本的發文函數
        from panel_article import pixnet_post
        res = await pixnet_post(email, pwd, title, content)
        return {"status": "success", "result": res}
    except Exception as e:
        return {"status": "fail", "error": str(e)}
