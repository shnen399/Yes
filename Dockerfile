FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 基本系統相依
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libglu1-mesa libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先裝 requirements 以利用快取
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright + Chromium
RUN pip install --no-cache-dir playwright && \
    python -m playwright install chromium

# 複製全部程式
COPY ..

# 啟動腳本確保可執行（存在就加權限，不存在也不會失敗）
RUN chmod +x startup.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
