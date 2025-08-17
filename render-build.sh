#!/usr/bin/env bash
set -e
pip install --no-cache-dir -r requirements.txt
# 安裝 Playwright 及其相依（Chromium）
playwright install --with-deps chromium
