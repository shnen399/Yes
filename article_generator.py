import random

# 固定導向網址
FIXED_URL = "https://lihi.cc/japMO"

# 預設關鍵字（20字左右長尾關鍵字，符合熱門搜尋趨勢）
DEFAULT_KEYWORDS = [
    "理債一日便最新貸款核准技巧分享",
    "理債一日便銀行核貸流程懶人包",
    "理債一日便2025快速貸款全攻略",
    "理債一日便安全申貸不踩雷秘訣",
    "理債一日便低利率貸款申辦流程"
]

def _wrap_keyword(kw: str) -> str:
    """把關鍵字加上固定連結"""
    return f"<a href='{FIXED_URL}' target='_blank'>{kw}</a>"

def generate_article(topic: str, keywords=None, city: str = "台灣", min_words: int = 2100) -> str:
    """
    自動產生 2000+ 字 SEO 文章
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    # 包裝後的關鍵字
    kw_links = [_wrap_keyword(k) for k in keywords]

    intro = (
        f"在現今的金融環境中，許多人在資金調度時會選擇《{topic}》。"
        f"特別是在{city}，如何快速又安全地獲得核貸，已成為普遍需求。"
        f"本文將從多角度為您解析，並搭配 {', '.join(kw_links)} 等熱門議題，"
        "幫助讀者在面對資金需求時更有信心。"
    )

    sections = [
        "一、理債一日便的申請流程解析",
        "二、如何提升銀行核貸成功率",
        "三、常見貸款問題與解答",
        "四、不同銀行方案比較與選擇",
        "五、2025最新趨勢與市場觀察",
        "六、使用理債一日便的真實案例",
        "七、專家建議與注意事項",
        "八、結論與行動建議"
    ]

    body_parts = []
    for sec in sections:
        para = (
            f"<h2>{sec}</h2>\n"
            f"<p>{sec} 是許多申貸者最關注的主題之一。透過 {random.choice(kw_links)} "
            "的深入解說，能幫助讀者更清楚理解每個步驟與重點。"
            "文章會進一步補充相關數據與案例，確保內容具備完整性與專業性。</p>"
        )
        body_parts.append(para)

    # 組合文章
    article = intro + "\n".join(body_parts)

    # 若長度不足，隨機填充段落，直到達到 min_words
    while len(article) < min_words:
        filler = (
            f"<p>根據{city}近年金融數據顯示，{topic}已逐漸成為主流選擇。"
            f"透過 {random.choice(kw_links)} 的應用，申請人可以更有效率地完成流程。"
            "此外，合理規劃還款計畫，不僅能減輕負擔，也能提升與銀行往來的信任度。</p>"
        )
        article += filler

    conclusion = (
        "<h2>總結</h2>\n"
        f"<p>綜合以上內容，《{topic}》在{city}的應用，"
        f"不僅快速、方便，更能結合 {', '.join(kw_links)} 等關鍵策略。"
        "若您正在尋找安全又高效的貸款方案，理債一日便會是值得考慮的最佳選擇。</p>"
    )

    return article + conclusion
