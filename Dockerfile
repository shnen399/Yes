# 已內建 Chromium/Firefox/WebKit 與 Playwright
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# 安裝你的 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# Render 會注入 $PORT
ENV PORT=10000

# 啟動 FastAPI（若入口不是 main:app，請改這裡）
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
