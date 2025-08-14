import os
import time
import httpx
from typing import List, Tuple, Dict
from fastapi import FastAPI
from xml.etree import ElementTree as ET

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -------------------- 設定 --------------------
# 你剛剛給的來源：Yahoo/UDN，ETtoday 那個網址是HTML清單，不是RSS，先忽略
NEWS_FEEDS = [
    "https://tw.news.yahoo.com/rss/",
    "https://udn.com/rssfeed/news/2/6638?ch=udn_ch2",
    # 若之後有中天/中時RSS，直接加在這裡
    # "https://xxx/your-cti-rss.xml",
]

# 理財型關鍵字（會拿來挑新聞標題/摘要）
KEYWORDS = [
    "理財", "投資", "基金", "ETF", "股票", "台積電", "債券", "美元",
    "利率", "通膨", "通縮", "房市", "房貸", "保險", "退休", "匯率",
    "AI", "晶片", "降息", "升息", "存股"
]

# 是否真的發到 PIXNET（環境變數 REAL_POST=true 才會真的發）
REAL_POST = os.getenv("REAL_POST", "false").lower() == "true"

# PIXNET OAuth（真的要發文時才會用到；帳密不足以發文）
PIX_CONSUMER_KEY    = os.getenv("PIXNET_CONSUMER_KEY", "")
PIX_CONSUMER_SECRET = os.getenv("PIXNET_CONSUMER_SECRET", "")
PIX_ACCESS_TOKEN    = os.getenv("PIXNET_ACCESS_TOKEN", "")
PIX_ACCESS_SECRET   = os.getenv("PIXNET_ACCESS_SECRET", "")
PIX_BLOG_NAME       = os.getenv("PIXNET_BLOG_NAME", "")  # 你的部落格帳號（例如 myname）

# （保留：若你要多帳號用）
def _read_accounts_from_env() -> List[Tuple[str, str]]:
    raw = os.getenv("PIXNET_ACCOUNTS", "").strip()
    out: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        if ":" in line:
            email, pwd = line.strip().split(":", 1)
            out.append((email, pwd))
    return out

# -------------------- 小工具 --------------------
def fetch_rss(url: str, timeout: int = 15) -> List[Dict]:
    """用內建 XML parser 取RSS，不需安裝額外套件"""
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers={"User-Agent": "news-bot/1.0"})
            r.raise_for_status()
            root = ET.fromstring(r.content)
    except Exception:
        return []

    # 兼容 <rss> 與 <feed>（Atom）
    items = []
    # RSS: /rss/channel/item
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        items.append({"title": title, "link": link, "summary": desc})

    # Atom: /feed/entry
    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = (link_el.get("href") if link_el is not None else "").strip()
        summary = (entry.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()
        items.append({"title": title, "link": link, "summary": summary})

    return items

def pick_articles(feeds: List[str], keywords: List[str], limit: int = 3) -> List[Dict]:
    """抓多個RSS並依關鍵字過濾，回傳前幾則"""
    pool: List[Dict] = []
    for url in feeds:
        pool.extend(fetch_rss(url))
        time.sleep(0.3)
    # 關鍵字過濾（標題+摘要）
    kw = [k.lower() for k in keywords]
    filtered = []
    for it in pool:
        content = (it.get("title", "") + " " + it.get("summary", "")).lower()
        if any(k in content for k in kw):
            filtered.append(it)

    # 去重（以link）
    seen = set()
    uniq = []
    for it in filtered:
        lk = it.get("link", "")
        if lk and lk not in seen:
            uniq.append(it)
            seen.add(lk)

    return uniq[:max(1, limit)]

def make_article(selected: List[Dict]) -> Dict[str, str]:
    """把選到的新聞組成一篇『理債一日便』風格文章"""
    if not selected:
        return {
            "title": "理債一日便｜今日市場筆記",
            "content": "今天沒有符合關鍵字的新聞。"
        }

    # 取第一則當主題
    main = selected[0]
    title = f"理債一日便｜{main.get('title','').strip()[:40]}（{time.strftime('%Y/%m/%d')}）"

    bullets = []
    refs = []
    for it in selected:
        t = it.get("title", "").strip()
        l = it.get("link", "").strip()
        bullets.append(f"• {t}")
        if l:
            refs.append(f"- {t}\n  {l}")

    body = f"""
【3行看重點】
{chr(10).join(bullets[:3])}

【快速解讀】
1) 這幾則新聞圍繞在市場熱門關鍵字（利率、ETF、AI、匯率或房市等），
   對短線氣氛與資金流向影響較大；波動環境下，分批與紀律仍是關鍵。
2) 若你偏保守：可用「核心債券＋衛星高股息ETF」做雙核心；偏積極：再加上台股/AI供應鏈ETF。
3) 外幣收息：留意升／降息循環與匯率風險，採「分散幣別＋定期定額」較穩。

【簡易配置範例（非投顧建議）】
- 現金部位：20–30%
- 核心債券：30–40%（投資級債、美元或全球綜合債）
- 股息ETF：20–30%（台股高股息/全球股息擇一或並行）
- 衛星主題：10–20%（AI、半導體、關鍵零組件）
- 風險控管：每月一次再平衡，單一標的≦20%

【參考來源】
{chr(10).join(refs) if refs else "（無）"}

（本文為自動彙整摘要與一般性理財整理，非個別投資建議。）
""".strip()

    return {"title": title, "content": body}

# -------------------- 發文（真正上 PIXNET 時才用） --------------------
def really_post_to_pixnet(title: str, content: str) -> Dict:
    """
    真的要發文到 PIXNET 需使用官方 API（OAuth 1.0a）。
    - 端點範例：POST https://emma.pixnet.cc/blog/articles?format=json
    - 必填參數：title, body, blog_name 等
    這裡先檢查憑證是否齊全；若未齊全就提示你補環境變數。
    """
    need = [PIX_CONSUMER_KEY, PIX_CONSUMER_SECRET, PIX_ACCESS_TOKEN, PIX_ACCESS_SECRET, PIX_BLOG_NAME]
    if not all(need):
        return {
            "status": "need_credentials",
            "message": "尚未設定 PIXNET OAuth 憑證（CONSUMER/ACCESS/ BLOG_NAME）。請先設定環境變數後再打 REAL_POST=true。",
        }

    # 若要實作簽名，可改用 requests-oauthlib 或自己帶 OAuth1 簽章。
    # Render 預設沒裝額外套件，這裡僅示意回傳，避免簽名失敗卡住部署。
    # 你要我幫你切換到 requests-oauthlib 版本也可以，告訴我就改成可直接發文的實作。
    return {
        "status": "dry-run",
        "message": "伺服器已準備好，但目前為無外部套件版本。建議改用 requests-oauthlib 以便完成 OAuth 簽名送出。",
        "preview": {"title": title, "content": content[:200] + "..."},
    }

# -------------------- API --------------------
@app.get("/")
async def root():
    return {"message": "PIXNET 自動發文系統已啟動"}

@app.get("/test_accounts")
async def test_accounts():
    return {"accounts": _read_accounts_from_env()}

@app.post("/post_article")
async def post_article():
    # 1) 抓新聞 + 關鍵字挑選
    chosen = pick_articles(NEWS_FEEDS, KEYWORDS, limit=3)
    # 2) 生成文章
    article = make_article(chosen)

    # 3) 是否真的發
    if REAL_POST:
        result = really_post_to_pixnet(article["title"], article["content"])
        return {
            "mode": "REAL_POST",
            "result": result,
            "picked": chosen,
        }

    # 預設：不真的發文，先回傳預覽
    return {
        "mode": "PREVIEW_ONLY",
        "article": article,
        "picked": chosen,
        "hint": "要真的發文：請設定 PIXNET OAuth 憑證 + REAL_POST=true。",
    }
