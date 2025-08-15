# ====== 新增：cookie 正規化小工具 ======
import json
from typing import List, Dict, Any, Optional

def _normalize_cookies(
    cookies: Any,
    default_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    接受多種 cookies 形式，轉成 Playwright 可用的 list[Cookie]。
    支援：
      - dict 形式（name->value） ＊會需要 default_url 才能注入
      - list[dict]（每個 dict 內含 name/value 及 domain/path 或 url）
      - JSON 字串（上面任一種的 JSON）
    若需要注入到特定站台但缺少 domain/path，會用 default_url 當作 url。
    """
    if cookies is None:
        return []

    # 如果是字串，試著當 JSON 解析
    if isinstance(cookies, str):
        cookies = cookies.strip()
        if not cookies:
            return []
        try:
            cookies = json.loads(cookies)
        except Exception:
            # 也可能是 "name=value; name2=value2" 這種；簡單切一下
            kv = [c.strip() for c in cookies.split(";") if "=" in c]
            as_dict = dict(s.split("=", 1) for s in kv)
            cookies = as_dict

    # dict(name->value)
    if isinstance(cookies, dict):
        if not default_url:
            raise ValueError("注入 cookies 需要 default_url（或改用含 domain/url 的 list 格式）")
        return [{"name": k, "value": str(v), "url": default_url} for k, v in cookies.items()]

    # list[dict]
    if isinstance(cookies, list):
        norm: List[Dict[str, Any]] = []
        for c in cookies:
            # 期待至少有 name/value，再搭配 url 或 domain/path
            if not isinstance(c, dict) or "name" not in c or "value" not in c:
                continue
            item = {"name": c["name"], "value": str(c["value"])}
            if "url" in c:
                item["url"] = c["url"]
            else:
                # 若沒 url，試著用 domain/path；再不然 fallback 到 default_url
                if "domain" in c:
                    item["domain"] = c["domain"]
                if "path" in c:
                    item["path"] = c["path"]
                if "domain" not in item and "url" not in item:
                    if not default_url:
                        raise ValueError("cookie 缺少 url/domain，且沒有提供 default_url")
                    item["url"] = default_url
            norm.append(item)
        return norm

    # 其他型態不支援
    return []

# ====== 取預設站台（注入 cookies 時會用）======
import os
PIXNET_BASE_URL = os.getenv("PIXNET_BASE_URL") or os.getenv("BLOG_BASE_URL") or "https://panel.pixnet.cc"
HEADLESS = (os.getenv("PIXNET_HEADLESS") or "auto").lower()  # 你原本的 headless 控制可保留

# ====== 覆蓋：post_article_once（新增 cookies: Any = None）======
from playwright.async_api import async_playwright

async def post_article_once(keyword: str, commit: bool = False, cookies: Any = None):
    """
    單次發文流程。
    新增 cookies 參數：可為 dict / list[dict] / JSON 字串。
    """
    title_text = f"{keyword}－自動發文測試"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=(HEADLESS != "false" and HEADLESS != "off")
        )
        # 建立 context 並注入 cookies（若有）
        context = await browser.new_context()

        try:
            cookie_list = _normalize_cookies(cookies, default_url=PIXNET_BASE_URL)
            if cookie_list:
                await context.add_cookies(cookie_list)
        except Exception as e:
            # 注入 cookies 失敗不讓流程整個掛掉，回傳清楚錯誤即可
            await context.close()
            await browser.close()
            return False, f"cookies 解析/注入失敗：{e}"

        page = await context.new_page()

        try:
            # ===== 下面維持你原本的動作：登入/開編輯頁/填標題/填內文/送出 =====
            # 例：進到文章編輯頁
            await page.goto(PIXNET_BASE_URL, wait_until="domcontentloaded")

            # 等待編輯頁載入、填標題（你已有的 fill_title_with_fallbacks 可直接呼叫）
            try:
                await fill_title_with_fallbacks(page, keyword)  # 你前面已加入的函式
            except Exception:
                await context.close()
                await browser.close()
                return False, '標題錯誤：找不到標題輸入框（編輯頁面可能改版）'

            # TODO: 這裡接你原本的 CKEditor 內文填寫與發佈流程
            # await _fill_ckeditor_in_iframe_or_div(page, html=...)  # 你原本的內容填入函式
            # if commit: ... # 真發佈

            # 假裝有文章網址（真發佈時換成成功的文章 URL）
            article_url = "https://www.pixnet.net/blog/post/xxxxxxxx"

            await context.close()
            await browser.close()
            return True, article_url

        except Exception as e:
            await context.close()
            await browser.close()
            return False, f"流程錯誤：{e}"
