# 直接用已內建 Chromium/依賴的 Playwright 官方映像
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy
WORKDIR /app
# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 拷貝全部程式碼
COPY . .
# Render 會幫你設好 $PORT，但我們用固定 10000 也可（你之前就是 10000）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
