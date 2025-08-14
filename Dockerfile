FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
# 安裝系統依賴（單行避免續行錯誤）
RUN apt-get update && apt-get install -y --no-install-recommends wget curl ca-certificates gnupg xdg-utils libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 libpangocairo-1.0-0 libpango-1.0-0 libcairo2 libatspi2.0-0 && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js 18（Playwright 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*
# Python 依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 安裝 Playwright + Chromium（更穩定的三步法）
RUN pip install --no-cache-dir playwright && \
    python -m playwright install-deps && \
    python -m playwright install chromium
# 複製專案內容
COPY . /app
# 確保腳本可執行
RUN chmod +x /app/startup.sh /app/render-build.sh || true
# 啟動（Render 會以 Start Command 執行）
CMD ["bash", "startup.sh"]
