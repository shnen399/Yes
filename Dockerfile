FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/opt/render/.cache/ms-playwright

# 系統相依套件（字型+瀏覽器依賴）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils \
    fonts-liberation fonts-unifont fonts-ubuntu \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libxrender1 libxshmfence1 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Python 環境與依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir playwright && python -m playwright install --with-deps chromium

COPY . /app

CMD ["bash", "startup.sh"]
