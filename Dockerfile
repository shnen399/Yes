# syntax=docker/dockerfile:1.7

# 輕量基底
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 1) 一次裝好 Playwright 需要的系統依賴（較少變動→可快取）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libglu1-mesa libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) 先安裝 requirements（較少變動→可快取）
#    使用 BuildKit 的 cache，加速 pip 下載
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 3) 安裝 Playwright + Chromium（很大，但不常變→可快取）
RUN pip install --no-cache-dir playwright && \
    python -m playwright install chromium

# 4) 最後才複製整個專案（最常變→放最後，避免破壞上面快取）
COPY . .

# 5) 確保啟動腳本可執行
RUN chmod +x startup.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
