#!/usr/bin/env bash
set -eux
python -V
echo "Build steps completed."
#!/usr/bin/env bash
pip install -r requirements.txt
playwright install --with-deps chromium
