#!/usr/bin/env bash
set -e

pip install -r requirements.txt

mkdir -p bin
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz
tar xf ffmpeg.tar.xz
mv ffmpeg-*-static/ffmpeg bin/ffmpeg
mv ffmpeg-*-static/ffprobe bin/ffprobe
rm -rf ffmpeg.tar.xz ffmpeg-*-static
chmod +x bin/ffmpeg bin/ffprobe

curl -fsSL https://deno.land/install.sh | sh

echo "Build complete!"
