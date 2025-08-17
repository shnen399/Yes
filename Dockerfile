# 用 Playwright + Chromium 官方映像
FROM mcr.microsoft.com/playwright/python:v1.49.0-focal

WORKDIR /app

# 先裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製全部程式
COPY . .

# Render 會用到的對外埠（你目前就是 10000）
EXPOSE 10000

# 直接啟動 FastAPI（不再用 startup.sh）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
