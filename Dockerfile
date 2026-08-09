# ใช้ Python 3.10 slim เป็นฐาน (เบาและรวดเร็ว)
FROM python:3.10-slim

# ติดตั้ง ffmpeg และเครื่องมือพื้นฐานจากระบบปฏิบัติการโดยตรง (ป้องกันปัญหา -11 Segfault)
RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# ติดตั้ง Deno สำหรับใช้แก้บล็อก YouTube ของ yt-dlp
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# ตั้งค่าพื้นที่ทำงาน
WORKDIR /app

# คัดลอกและติดตั้ง Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกซอร์สโค้ดทั้งหมด
COPY . .

# กำหนดคำสั่งรัน
CMD ["python", "musicbot.py"]
