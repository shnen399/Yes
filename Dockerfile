FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安裝 Playwright/Chromium 需要的系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
    libxss1 libxtst6 libglib2.0-0 libpangocairo-1.0-0 libglu1-mesa \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright（不帶 --with-deps）
RUN pip install --no-cache-dir playwright
RUN python -m playwright install chromium

# 複製程式碼並給啟動檔執行權限
COPY . .
RUN chmod +x startup.sh pw_setup.sh render-build.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
