#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Download and extract Deno Linux binary using Python
PYTHON_BIN=$(which python3 || which python)
$PYTHON_BIN -c "import urllib.request, zipfile, os; os.makedirs('bin', exist_ok=True); urllib.request.urlretrieve('https://github.com/denoland/deno/releases/download/v2.1.4/deno-x86_64-unknown-linux-gnu.zip', 'deno.zip'); zipfile.ZipFile('deno.zip').extractall('bin'); os.chmod('bin/deno', 0o755); os.remove('deno.zip')"

echo "Build complete! Requirements and Deno installed successfully."
