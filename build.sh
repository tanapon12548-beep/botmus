#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# à¸”à¸²à¸§à¸™à¹Œà¹‚à¸«à¸¥à¸”à¹à¸¥à¸°à¹à¸•à¸à¹„à¸Ÿà¸¥à¹Œ Deno Linux Binary à¸”à¹‰à¸§à¸¢ Python (à¸à¸²à¸£à¸±à¸™à¸•à¸µ 100% à¸šà¸™ Render à¹„à¸¡à¹ˆà¸•à¹‰à¸­à¸‡à¸žà¸¶à¹ˆà¸‡ unzip)
python3 -c "import urllib.request, zipfile, os; os.makedirs('bin', exist_ok=True); urllib.request.urlretrieve('https://github.com/denoland/deno/releases/download/v2.1.4/deno-x86_64-unknown-linux-gnu.zip', 'deno.zip'); zipfile.ZipFile('deno.zip').extractall('bin'); os.chmod('bin/deno', 0o755); os.remove('deno.zip')"

echo "Build complete! Requirements and Deno installed."
