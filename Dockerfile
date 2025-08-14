# --- Base ---
FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # 將 Playwright 瀏覽器裝在 Render 的快取目錄，避免每次重下
    PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright
# --- 系統相依套件（修正版） ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 \
    libxshmfence1 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 \
 && rm -rf /var/lib/apt/lists/*
# --- 安裝 Node 18（Playwright 需要） ---
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*
# --- Python 依賴 ---
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# --- 安裝 Playwright 及瀏覽器 ---
# 1) 安裝 Python 版 playwright
RUN pip install --no-cache-dir playwright \
 && python -m playwright install --with-deps chromium
# 你的專案檔案
COPY . /app
# Render 會用 Start Command 啟動；這裡提供預設 CMD（可被覆蓋）
# 若你的主程式是 main.py、app 物件叫 app：
CMD ["bash", "startup.sh"]
