#!/usr/bin/env bash
# สคริปต์ติดตั้ง dependencies สำหรับ Render

# ติดตั้ง FFmpeg
apt-get update && apt-get install -y ffmpeg

# ติดตั้ง Deno (จำเป็นสำหรับ yt-dlp YouTube extraction)
curl -fsSL https://deno.land/install.sh | sh
export DENO_INSTALL="$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"

# ติดตั้ง Python packages
pip install -r requirements.txt
