# ---- 基本環境 ----
FROM python:3.11-slim

# 1) 系統依賴（Playwright/Chromium 需要）
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
 && rm -rf /var/lib/apt/lists/*

# 2) 安裝 Node.js 18（Playwright 需要 >=16）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs

# 3) Python 依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) 指定 Playwright 瀏覽器安裝位置（避免平台權限問題）
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 5) 安裝 Playwright 的 Chromium（改用 npx，較穩定）
RUN npx playwright install --with-deps chromium

# 6) 拷貝專案檔案
COPY . .

# 7) 啟動 FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
