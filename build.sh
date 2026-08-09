#!/usr/bin/env bash
set -e

pip install -r requirements.txt

mkdir -p bin

# 1. à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡ FFmpeg static binary à¸¥à¸‡à¹ƒà¸™ bin/
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz
tar xf ffmpeg.tar.xz
mv ffmpeg-*-static/ffmpeg bin/ffmpeg
mv ffmpeg-*-static/ffprobe bin/ffprobe
rm -rf ffmpeg.tar.xz ffmpeg-*-static

# 2. à¸•à¸´à¸”à¸•à¸±à¹‰à¸‡ Deno binary à¸¥à¸‡à¹ƒà¸™ bin/ à¹‚à¸”à¸¢à¸•à¸£à¸‡ (à¹€à¸žà¸·à¹ˆà¸­à¹ƒà¸«à¹‰ yt-dlp à¹à¸à¹‰ JS Challenge à¹„à¸”à¹‰)
curl -fsSL https://github.com/denoland/deno/releases/download/v2.1.4/deno-x86_64-unknown-linux-gnu.zip -o deno.zip
unzip -o deno.zip -d bin
rm -f deno.zip

chmod +x bin/ffmpeg bin/ffprobe bin/deno

echo "Build complete! FFmpeg and Deno installed in bin/"
