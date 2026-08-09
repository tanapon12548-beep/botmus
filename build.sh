#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Download and extract Deno and FFmpeg using Python
PYTHON_BIN=$(which python3 || which python)

$PYTHON_BIN -c "import urllib.request, zipfile, os; os.makedirs('bin', exist_ok=True); urllib.request.urlretrieve('https://github.com/denoland/deno/releases/download/v2.1.4/deno-x86_64-unknown-linux-gnu.zip', 'deno.zip'); zipfile.ZipFile('deno.zip').extractall('bin'); os.chmod('bin/deno', 0o755); os.remove('deno.zip')"

$PYTHON_BIN -c "import urllib.request, tarfile, os, shutil; os.makedirs('bin', exist_ok=True); urllib.request.urlretrieve('https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz', 'ffmpeg.tar.xz'); tar = tarfile.open('ffmpeg.tar.xz'); tar.extractall(); tar.close(); ffmpeg_dir = [d for d in os.listdir('.') if d.startswith('ffmpeg-') and os.path.isdir(d)][0]; shutil.move(os.path.join(ffmpeg_dir, 'ffmpeg'), 'bin/ffmpeg'); os.chmod('bin/ffmpeg', 0o755); shutil.rmtree(ffmpeg_dir); os.remove('ffmpeg.tar.xz')"

echo "Build complete! Requirements, Deno, and FFmpeg installed successfully."
