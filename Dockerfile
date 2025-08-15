# syntax=docker/dockerfile:1.7
# 內建好 Playwright + Chromium 的官方映像
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /app

# 先裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 讓啟動腳本可執行（若不存在也不報錯）
RUN chmod +x startup.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
