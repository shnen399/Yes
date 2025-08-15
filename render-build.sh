
#!/usr/bin/env bash
set -eux

# 顯示 Python 版本
python -V

# 安裝依賴
pip install --upgrade pip
pip install -r requirements.txt

# 安裝 Playwright 及 Chromium 瀏覽器
playwright install --with-deps chromium
