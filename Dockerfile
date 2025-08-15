# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# (可留可刪) 基本工具；真的要最小也可全刪，因為步驟 3 的 --with-deps 會自己裝
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates xdg-utils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先安裝 requirements（建議把 playwright 也寫進 requirements.txt）
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 🔴 這一步很關鍵：安裝 Playwright + Chromium + 系統相依套件
#    用 python -m 執行並加上 --with-deps
RUN python -m playwright install --with-deps chromium

# 複製程式碼（放最後，讓上面層可被快取）
COPY . .

# 啟動腳本可執行
RUN chmod +x startup.sh || true

EXPOSE 10000
CMD ["bash", "startup.sh"]
