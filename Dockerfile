# ---- 使用 Playwright 官方基底映像 ----
FROM mcr.microsoft.com/playwright/python:v1.48.2-focal

# 設定工作目錄
WORKDIR /app

# 複製需求檔並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 預設啟動指令 (FastAPI + Uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
