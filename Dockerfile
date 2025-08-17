# 使用 Playwright 官方提供的 Python 基底映像
FROM mcr.microsoft.com/playwright/python:focal

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
