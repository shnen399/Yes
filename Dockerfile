# ---- 基本建置 ----
FROM python:3.11-slim

# 安裝 Playwright 需要的系統相依套件
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libglib2.0-0 libatk1.0-dev libgtk-3-dev libnotify-dev libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright + Chromium
RUN pip install playwright && playwright install --with-deps chromium

# 複製所有程式（包含 panel_article.py 等）
COPY . .

# 用 Render 的 PORT 環境變數啟動（預設 10000）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
