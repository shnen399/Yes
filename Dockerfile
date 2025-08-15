# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安裝 Playwright/Chromium 會用到的系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libxss1 libxtst6 libglib2.0-0 libpangocairo-1.0-0 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先裝 Python 套件（requirements.txt 內若已含 playwright 可省略下一行安裝）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 || (pip install --no-cache-dir -r requirements.txt --break-system-packages)

# 確保 Playwright 安裝完成（即使 requirements 沒列也會裝到）
RUN pip install --no-cache-dir playwright \
 || (pip install --no-cache-dir playwright --break-system-packages)

# 安裝 Chromium（同時安裝缺的依賴）
RUN python -m playwright install --with-deps chromium

# 複製專案與腳本、給執行權限
COPY . .
RUN chmod +x startup.sh pw_setup.sh render-build.sh || true

# Render 會忽略，但標記一下常用埠（若你用 uvicorn 預設 8000 就改 8000）
EXPOSE 10000

# 用你的啟動腳本啟動服務
CMD ["bash", "startup.sh"]
