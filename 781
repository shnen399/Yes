# ---- Base ----
FROM python:3.11-slim

# 必要系統套件（Playwright/Chromium 依賴）
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 \
    libxshmfence1 libglib2.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright + Chromium（用 module 呼叫較穩）
RUN python -m pip install --no-cache-dir playwright \
 && python -m playwright install --with-deps chromium

# 複製所有程式（包含 main.py / panel_article.py）
COPY . .

# 用 Render 的 $PORT 啟動（千萬不要寫死 10000）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
