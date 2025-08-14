# 系統相依（精簡且不含字型，先確保能過）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg xdg-utils \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libxrender1 libxshmfence1 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 \
 && rm -rf /var/lib/apt/lists/*
