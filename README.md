# Render + FastAPI + Playwright

使用 Docker，在 **建置階段** 安裝 Playwright 的 Chromium。
部署到 Render 後直接可用，不會在 API 執行時才安裝瀏覽器。

## 端點
- GET /          ：存活檢查
- GET /healthz   ：健康檢查
- POST /post_article：開啟 example.com 並回傳標題

## 在 Render 部署
1. 專案根目錄包含：Dockerfile、requirements.txt、main.py、.dockerignore。
2. Render → New → Web Service，選這個 repo。偵測到 Dockerfile 會走 Docker 模式。
3. Build/Start **留空**（若 UI 不讓留空，Start 可填：`uvicorn main:app --host 0.0.0.0 --port $PORT`）。
4. 部署完成後訪問 `/docs` 測試。
