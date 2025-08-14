# 和本地一致：Python 3.11 + Debian slim
FROM python:3.11-slim

# 基本環境（減少輸出緩衝、關閉 .pyc）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安裝基礎系統套件（精簡即可）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先裝 Python 依賴
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 暴露埠：Render 會注入 $PORT，這裡不用固定數字
EXPOSE 10000

# 啟動 FastAPI（Render 會將 $PORT 帶入）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
