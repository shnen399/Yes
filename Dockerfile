# ---- 基本建置 ----
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Playwright（你有用到）
RUN playwright install --with-deps chromium

# 這行要把「所有檔案」包含 panel_article.py 拷進映像
COPY . .

# 啟動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
