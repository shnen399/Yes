# ---- 基本環境 ----
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1) 系統依賴（含 Playwright 需求 + 字型）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation fonts-unifont fonts-noto-cjk \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
 && rm -rf /var/lib/apt/lists/*

# 2) 安裝 Node.js 18（Playwright 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# 3) Python 依賴
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) 安裝 Playwright 瀏覽器（用 Python 版本）
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN python -m playwright install --with-deps chromium

# 5) 複製專案
COPY . .

# 6) 啟動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
