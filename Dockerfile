FROM python:3.11-slim

# 安裝 Chromium 及 Playwright 所需系統套件
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils fonts-liberation \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-6 \
    libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 \
    libxfixes3 libxrandr2 libxrender1 libxshmfence1 libglib2.0-0 \
    libatk1.0-data libatk-bridge2.0-0 libpangocairo-1.0-0 \
    libpango-1.0-0 libcairo2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 安裝 Playwright 及 Chromium
RUN pip install playwright && python -m playwright install --with-deps chromium
COPY . .
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
