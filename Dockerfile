FROM python:3.11-slim

# 安裝系統相依套件（Playwright 需要）
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js（Playwright 需要 Node.js >=18）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 安裝 Python 依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 安裝 Playwright 及 Chromium 瀏覽器
RUN pip install playwright && playwright install --with-deps chromium

# 複製專案檔案
COPY . .

# 啟動 FastAPI 服務
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
