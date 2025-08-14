# main.py - FastAPI + (可選)排程 + RSS 摘要 + 預覽/真發文切換

import os
import asyncio
import httpx
from typing import List, Tuple, Dict
from fastapi import FastAPI, Request, HTTPException

# ---------------- 基本設定 ----------------
app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 讀帳號（環境變數優先）
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    """
    環境變數 PIXNET_ACCOUNTS：
      多行，每行格式  email:password
    例：
      t0970313177@gmail.com:co13572888
    """
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    out: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        if ":" in line:
            email, pw = line.strip().split(":", 1)
            out.append((email.strip(), pw.strip()))
    return out


# 允不允許「真發文」
def allow_real_post() -> bool:
    # ALLOW_POST=1 代表允許真發文；其他值或沒設＝只做預覽
    return os.getenv("ALLOW_POST", "0") == "1"


# 此次呼叫是否要求 commit（加上 ?commit=1 啟用）
def should_commit(request: Request) -> bool:
    return request.query_params.get("commit") == "1"


# ---------------- RSS 抓新聞（含關鍵字過濾） ----------------
# 你之前貼的 3 個來源 +「中天」(CtiTV) 一個來源
RSS_SOURCES_DEFAULT = [
    "https://tw.news.yahoo.com/rss/",
    "https://udn.com/rssfeed/news/2/6638?ch=udn_ch2",
    "https://www.ettoday.net/news/news-list-2024-01-01-1.htm?from=rss",
    "https://gotv.ctitv.com.tw/rss/news.xml",  # 中天
]

def _rss_sources() -> List[str]:
    """
    可用環境變數 RSS_SOURCES 覆蓋，逗號分隔
    """
    raw = os.getenv("RSS_SOURCES", "")
    if raw.strip():
        return [s.strip() for s in raw.split(",") if s.strip()]
    return RSS_SOURCES_DEFAULT

def _want_keywords() -> List[str]:
    """
    NEWS_KEYWORDS：逗號分隔關鍵字（任一符合即保留），沒設就不過濾
    例：NEWS_KEYWORDS=AI,ETF,選舉,台積電
    """
    raw = os.getenv("NEWS_KEYWORDS", "")
    return [k.strip() for k in raw.split(",") if k.strip()]

async def fetch_url_text(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""

def _extract_items_from_xml(xml_text: str) -> List[Dict[str, str]]:
    """
    極簡 XML 解析：嘗試從常見 RSS/Atom 中抓 title/link
    不依賴第三方套件，盡量做寬鬆解析
    """
    items: List[Dict[str, str]] = []
    if not xml_text:
        return items

    lower = xml_text.lower()

    # 很多 RSS 是 <item>...<title>...<link>...
    # 也有 Atom 是 <entry>...<title>...<link href="..."/>
    # 這裡做兩套簡單抓法（非嚴格，但足以生成示範內容）
    def _between(s: str, start: str, end: str, pos: int = 0):
        i = s.find(start, pos)
        if i == -1: 
            return "", -1
        j = s.find(end, i + len(start))
        if j == -1:
            return "", -1
        return s[i + len(start): j], j + len(end)

    pos = 0
    # 先試 RSS <item>
    while True:
        seg, pos = _between(lower, "<item", "</item>", pos)
        if pos == -1: 
            break
        # 從原文取同區段（用 lower 的邊界去對原文 slice）
        start_idx = lower.find("<item", pos - len("</item>") - len(seg) - 5)
        end_idx = lower.find("</item>", start_idx) + len("</item>")
        if start_idx == -1 or end_idx == -1:
            continue
        raw_seg = xml_text[start_idx:end_idx]

        # 抓 title
        title, _ = _between(raw_seg, "<title>", "</title>", 0)
        # 抓 link（先試 <link>URL</link>）
        link, _ = _between(raw_seg, "<link>", "</link>", 0)
        if not link:
            # 有些 RSS 用 <guid> 或 atom link
            link, _ = _between(raw_seg, 'href="', '"', 0)
        title = title.strip().strip("<![CDATA[").strip("]]>").strip()
        link = link.strip().strip("<![CDATA[").strip("]]>").strip()
        if title:
            items.append({"title": title, "link": link or ""})

    # 若完全沒抓到，再試 Atom <entry>
    if not items:
        pos = 0
        while True:
            seg, pos = _between(lower, "<entry", "</entry>", pos)
            if pos == -1: 
                break
            start_idx = lower.find("<entry", pos - len("</entry>") - len(seg) - 5)
            end_idx = lower.find("</entry>", start_idx) + len("</entry>")
            if start_idx == -1 or end_idx == -1:
                continue
            raw_seg = xml_text[start_idx:end_idx]

            title, _ = _between(raw_seg, "<title>", "</title>", 0)
            link, _ = _between(raw_seg, 'href="', '"', 0)
            title = title.strip().strip("<![CDATA[").strip("]]>").strip()
            link = link.strip().strip("<![CDATA[").strip("]]>").strip()
            if title:
                items.append({"title": title, "link": link or ""})

    return items

async def collect_headlines(max_items: int = 12) -> List[Dict[str, str]]:
    """
    從多個 RSS 來源抓資料，合併後做關鍵字過濾與去重
    """
    sources = _rss_sources()
    keywords = _want_keywords()

    out: List[Dict[str, str]] = []
    seen_title = set()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        texts = await asyncio.gather(*[fetch_url_text(client, u) for u in sources])

    for txt in texts:
        for it in _extract_items_from_xml(txt):
            title = it.get("title", "").strip()
            if not title or title in seen_title:
                continue
            if keywords:
                if not any(kw in title for kw in keywords):
                    continue
            seen_title.add(title)
            out.append(it)
            if len(out) >= max_items:
                break
        if len(out) >= max_items:
            break

    return out


def build_article_from_headlines(items: List[Dict[str, str]]) -> Dict[str, str]:
    """
    產生文章：標題 + 內文（含連結列表）
    """
    if not items:
        title = "今日快訊整理（無符合關鍵字）"
        content = "目前沒有符合關鍵字的新聞。"
        return {"title": title, "content": content}

    # 標題：第一則 + 今日日期
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    date_str = datetime.now(tz).strftime("%Y/%m/%d")
    title = f"理偵一日便｜{items[0]['title']}（{date_str}）"

    # 內容：三行重點 + 連結清單
    lines = ["【3行看重點】"]
    for i, it in enumerate(items[:3], 1):
        lines.append(f"{i}. {it['title']}")

    lines.append("\n【延伸閱讀】")
    for it in items:
        link = it.get("link") or ""
        if link:
            lines.append(f"- {it['title']}  {link}")
        else:
            lines.append(f"- {it['title']}")

    content = "\n".join(lines)
    return {"title": title, "content": content}


# ---------------- PIXNET 真發文（示範 stub） ----------------
async def pixnet_post_article(account: Tuple[str, str], title: str, content: str) -> Tuple[bool, str]:
    """
    這裡放「真發文」邏輯（目前為範例 stub，回傳成功＋假網址）。
    你未來若要真的發到 PIXNET，建議在這裡實作：
      - 使用 Selenium/Playwright 登入後台，建立新文章並貼上內容
      - 或若有 API/Email投稿/IFTTT 方案，也可以在此呼叫
    """
    email, _pwd = account
    # TODO: 換成真實發文流程
    fake_url = f"https://{email.split('@')[0]}.pixnet.net/blog/post/auto-{os.urandom(2).hex()}"
    return True, fake_url


# ---------------- API ----------------
@app.get("/")
async def root():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.get("/test_accounts")
async def test_accounts():
    return {"accounts": _read_accounts_from_env()}

@app.post("/post_article")
async def post_article(request: Request):
    """
    預設：預覽模式（不發文），回傳將要發的 title/content。
    啟用真發文條件：
      1) Render 環境變數 ALLOW_POST=1
      2) 呼叫時加上 ?commit=1
    """
    accounts = _read_accounts_from_env()
    if not accounts:
        raise HTTPException(status_code=400, detail="未偵測到帳號（請設定環境變數 PIXNET_ACCOUNTS）")

    # 抓新聞 → 組文章
    items = await collect_headlines(max_items=12)
    article = build_article_from_headlines(items)
    title, content = article["title"], article["content"]

    # 判斷是否真發文
    will_commit = allow_real_post() and should_commit(request)

    if will_commit:
        ok, url_or_msg = await pixnet_post_article(accounts[0], title, content)
        mode = "POST_REAL"
        if ok:
            return {"status": "success", "mode": mode, "title": title, "url": url_or_msg}
        return {"status": "fail", "mode": mode, "title": title, "error": url_or_msg}

    # 預覽模式
    return {
        "status": "success",
        "mode": "PREVIEW_ONLY",
        "article": {"title": title, "content": content},
        "hint": "要真發文：設 ALLOW_POST=1 並以 /post_article?commit=1 呼叫",
    }


# ---------------- 本機/Termux 執行（Render 用 start 指令即可） ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
