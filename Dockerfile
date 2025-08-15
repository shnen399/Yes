# 用最新 Playwright + Chromium 的官方映像
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# 先安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案全部檔案
COPY . .

# 確保 startup.sh 可執行
RUN chmod +x startup.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
