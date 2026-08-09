#!/usr/bin/env bash
set -e

# à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡ Python packages
pip install -r requirements.txt

# à¸”à¸²à¸§à¸™à¹Œà¹‚à¸«à¸¥à¸” FFmpeg static binary
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz
tar xf ffmpeg.tar.xz
mv ffmpeg-*-static/ffmpeg /usr/local/bin/ffmpeg
mv ffmpeg-*-static/ffprobe /usr/local/bin/ffprobe
rm -rf ffmpeg.tar.xz ffmpeg-*-static

# à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡ Deno
curl -fsSL https://deno.land/install.sh | sh

echo "Build complete!"
