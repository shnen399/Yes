# ==== 基底映像 ====
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ==== 系統相依（給 Playwright / Chromium 用）====
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libnss3 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 \
    libx11-6 libx11-xcb1 libxcb1 libxcursor1 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libu2f-udev libpci3 libxss1 libappindicator3-1 \
 && rm -rf /var/lib/apt/lists/*

# （可選）安裝 Node.js 18；有些套件會用到，留著較保險
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

# ==== Python 依賴 ====
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ==== 安裝 Playwright 的 Chromium（注意：不要 --with-deps）====
RUN python -m playwright install chromium

# ==== 專案檔 ====
COPY . .

# ==== 啟動 ====
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
