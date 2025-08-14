# 讓 Render / 本地一致：Python 3.11 + Debian slim
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安裝 Playwright/Chromium 需要的系統相依套件（一併裝好）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 \
    libxshmfence1 libxkbcommon0 libpango-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libfreetype6 libfontconfig1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先安裝 Python 套件
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 並把 Chromium 下載進 image
RUN pip install playwright && playwright install chromium

# 複製程式碼
COPY . .

# Render / 本地統一對外埠號（改成 $PORT）
EXPOSE $PORT

# 啟動 FastAPI（改成使用 $PORT）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
