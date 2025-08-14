FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

# 系統相依套件（字型 + Chromium 依賴）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils \
    fonts-liberation fonts-unifont fonts-ubuntu \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libxrender1 libxshmfence1 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Node.js 18（Playwright 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Python 依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright + Chromium
RUN pip install --no-cache-dir playwright \
 && python -m playwright install --with-deps chromium

# 複製專案
COPY . /app

# 確保啟動/建置腳本有可執行權限
RUN chmod +x /app/startup.sh /app/render-build.sh || true

# 啟動（Render 會用 Start Command 覆蓋也沒關係）
CMD ["bash", "startup.sh"]
