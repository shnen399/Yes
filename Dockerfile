FROM python:3.11-slim

# 安裝系統相依套件（Playwright Chromium 需要）
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxrender1 libxshmfence1 \
 && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js 18（Playwright 需要）
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs

# 更新 pip
RUN pip install --upgrade pip

# 設定工作目錄
WORKDIR /app

# 複製需求檔並安裝 Python 套件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 安裝 Playwright 與 Chromium
RUN pip install playwright && playwright install --with-deps chromium

# 複製所有程式碼
COPY . .

# 啟動應用程式
CMD ["python", "main.py"]
