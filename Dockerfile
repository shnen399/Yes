# ---- 基本建置 ----
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 用 module 呼叫，較穩定
RUN python -m playwright install --with-deps chromium

# 把所有程式(含 panel_article.py)打包進容器
COPY . .

# 啟動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
