FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils fonts-liberation \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libnss3 libx11-6 libxi6 \
    libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxrandr2 libxrender1 libxshmfence1 libglib2.0-0 libgbm1 \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ➜ 把 Chromium 裝進映像（關鍵）
RUN python -m playwright install --with-deps chromium
COPY . .
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
