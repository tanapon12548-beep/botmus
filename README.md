# 🎵 คู่มือการใช้งาน Discord Music Bot

## 📋 สารบัญ
- [ติดตั้ง](#-การติดตั้ง)
- [ตั้งค่า](#-การตั้งค่า)
- [เริ่มใช้งาน](#-เริ่มใช้งาน)
- [คำสั่งทั้งหมด](#-คำสั่งทั้งหมด)
- [แก้ปัญหา](#-แก้ปัญหาเบื้องต้น)

---

## 📦 การติดตั้ง

### สิ่งที่ต้องมี
- **Python 3.10+** — [ดาวน์โหลด](https://www.python.org/downloads/)
- **FFmpeg** — ใช้สำหรับสตรีมเสียง
- **Deno** — ใช้สำหรับ YouTube extraction
- **Discord Bot Token** — สร้างได้ที่ [Discord Developer Portal](https://discord.com/developers/applications)

### 1. ติดตั้ง Python packages

```bash
pip install "discord.py[voice]" yt-dlp python-dotenv
```

### 2. ติดตั้ง FFmpeg

**Windows (ผ่าน winget):**
```bash
winget install --id Gyan.FFmpeg -e --source winget
```

**หรือดาวน์โหลดเอง:** [ffmpeg.org/download](https://ffmpeg.org/download.html) แล้วเพิ่มลง PATH

### 3. ติดตั้ง Deno

**Windows (ผ่าน winget):**
```bash
winget install --id DenoLand.Deno -e --source winget
```

> ⚠️ หลังติดตั้ง FFmpeg และ Deno **ต้องปิดแล้วเปิด terminal ใหม่** เพื่อให้ PATH อัพเดต

---

## ⚙️ การตั้งค่า

### 1. สร้างไฟล์ `.env`

สร้างไฟล์ `.env` ในโฟลเดอร์เดียวกับ `musicbot.py` แล้วใส่ Token ของบอท:

```env
DISCORD_TOKEN=ใส่_TOKEN_ของคุณที่นี่
```

### 2. เปิด Intents ใน Discord Developer Portal

1. เข้า [Discord Developer Portal](https://discord.com/developers/applications)
2. เลือกบอทของคุณ → **Bot** → เลื่อนไปที่ **Privileged Gateway Intents**
3. เปิด ✅ **MESSAGE CONTENT INTENT**

### 3. เชิญบอทเข้าเซิร์ฟเวอร์

1. ไปที่ **OAuth2** → **URL Generator**
2. เลือก Scopes: `bot`
3. เลือก Permissions: `Connect`, `Speak`, `Send Messages`, `Read Message History`
4. คัดลอก URL แล้วเปิดในเบราว์เซอร์เพื่อเชิญบอท

---

## 🚀 เริ่มใช้งาน

### รันบอท

```bash
py musicbot.py
```

เมื่อเห็นข้อความ `ล็อกอินสำเร็จในชื่อ ชื่อบอท#1234` แปลว่าบอทพร้อมใช้งาน!

### วิธีเล่นเพลง

1. **เข้า Voice Channel** ในเซิร์ฟเวอร์ Discord
2. พิมพ์คำสั่งในช่องแชท เช่น:
   ```
   !play ชื่อเพลงที่ต้องการ
   ```
3. บอทจะเข้าร่วมห้องและเล่นเพลงอัตโนมัติ 🎶

---

## 🎮 คำสั่งทั้งหมด

| คำสั่ง | ชื่อย่อ | ตัวอย่าง | หน้าที่ |
|---|---|---|---|
| `!play` | `!p` | `!p Never Gonna Give You Up` | เล่นเพลง หรือเพิ่มเข้าคิวถ้ากำลังเล่นอยู่ |
| `!skip` | `!s`, `!sk` | `!s` | ข้ามเพลงปัจจุบัน → เล่นเพลงถัดไปอัตโนมัติ |
| `!jump` | `!j` | `!j 3` | เลื่อนเพลงในคิวมาเล่นก่อน (เพลงอื่นยังอยู่) |
| `!queue` | `!q` | `!q` | ดูรายการเพลงในคิว |
| `!remove` | `!rm` | `!rm 2` | ลบเพลงลำดับที่ระบุออกจากคิว |
| `!clear` | `!cl` | `!cl` | ล้างคิวเพลงทั้งหมด |
| `!stop` | `!dc`, `!leave` | `!dc` | ล้างคิว + หยุดเพลง + บอทออกจากห้อง |
| `!help` | — | `!help` | แสดงรายการคำสั่งทั้งหมด |

### ระบบคิวเพลง 📋

- **ไม่จำกัดจำนวน** เพลงในคิว
- เมื่อเพลงปัจจุบันจบ → เพลงถัดไปในคิวจะเล่นอัตโนมัติ
- สามารถพิมพ์ **ชื่อเพลง** หรือ **URL จาก YouTube** ได้ทั้งสองแบบ

**ตัวอย่างการใช้งาน:**
```
!p เพลงรักเพลงหนึ่ง           → 🎵 กำลังเล่น: เพลงรักเพลงหนึ่ง
!p ลุงพล                       → 📋 เพิ่มเข้าคิว #1: ลุงพล
!p Shape of You                → 📋 เพิ่มเข้าคิว #2: Shape of You
!p Blinding Lights             → 📋 เพิ่มเข้าคิว #3: Blinding Lights
!q                             → 📋 คิวเพลง (3 เพลง): ...
!j 3                           → ⏩ ข้ามไปเล่น: Blinding Lights
!rm 1                          → 🗑️ ลบเพลง #1: ลุงพล ออกจากคิวแล้ว!
!s                             → ⏭️ ข้ามเพลง!
!dc                            → 🛑 ออกจากห้องและหยุดเล่นเพลงแล้ว
```

---

## 🔧 แก้ปัญหาเบื้องต้น

### ❌ `davey library needed in order to use voice`
```bash
pip install "discord.py[voice]"
```
ติดตั้ง package `davey` และ `PyNaCl` ที่จำเป็นสำหรับเสียง

### ❌ `ffmpeg is not recognized`
ติดตั้ง FFmpeg แล้ว **ปิดและเปิด terminal ใหม่**:
```bash
winget install --id Gyan.FFmpeg -e --source winget
```

### ❌ `No supported JavaScript runtime could be found`
ติดตั้ง Deno แล้ว **ปิดและเปิด terminal ใหม่**:
```bash
winget install --id DenoLand.Deno -e --source winget
```

### ❌ `คุณต้องเข้า Voice Channel ก่อนครับ!`
ต้องเข้า Voice Channel ก่อนแล้วค่อยพิมพ์คำสั่ง `!play`

### ❌ `คิวเต็มแล้ว!`
คิวรองรับสูงสุด 5 เพลง — ใช้ `!remove` หรือ `!clear` เพื่อเคลียร์คิวก่อน

### ❌ บอทไม่ตอบคำสั่ง
1. ตรวจสอบว่าเปิด **MESSAGE CONTENT INTENT** ใน Developer Portal แล้ว
2. ตรวจสอบว่าใช้ prefix `!` นำหน้าคำสั่ง
3. ตรวจสอบว่าบอทมีสิทธิ์อ่านข้อความในช่องนั้น

---

## 📁 โครงสร้างไฟล์

```
bot/
├── musicbot.py        # ไฟล์หลักของบอท
├── requirements.txt   # รายการ Python packages
├── build.sh           # สคริปต์ติดตั้งสำหรับ Render
├── .gitignore         # ไฟล์ที่ไม่ต้อง push ขึ้น GitHub
├── .env               # เก็บ Token (ห้ามแชร์! ไม่ถูก push ขึ้น GitHub)
└── README.md          # คู่มือการใช้งาน (ไฟล์นี้)
```

> ⚠️ **ข้อควรระวัง:** ห้ามแชร์ไฟล์ `.env` หรือ Token ของบอทให้ใครเด็ดขาด!

---

## ☁️ Deploy บน Render (ฟรี)

ทำให้บอทรัน 24/7 โดยไม่ต้องเปิดคอมตลอด

### เครื่องมือที่ต้องใช้ (ฟรีทั้งหมด)

| เครื่องมือ | หน้าที่ | ลิงก์ |
|---|---|---|
| **GitHub** | ฝากโค้ดเพื่อส่งต่อไป Render | [github.com](https://github.com/) |
| **Render** | รันบอทบนเซิร์ฟเวอร์ฟรี | [render.com](https://render.com/) |
| **UptimeRobot** | Ping ทุก 5 นาที ไม่ให้ Render หลับ | [uptimerobot.com](https://uptimerobot.com/) |

### ขั้นตอนที่ 1: Push โค้ดขึ้น GitHub

```bash
cd D:\test\bot
git init
git add .
git commit -m "Discord Music Bot"
git branch -M main
git remote add origin https://github.com/ชื่อคุณ/discord-music-bot.git
git push -u origin main
```

> ⚠️ ตรวจสอบให้แน่ใจว่า `.env` อยู่ใน `.gitignore` แล้ว — Token จะได้ไม่ถูก push ขึ้น GitHub

### ขั้นตอนที่ 2: สร้าง Web Service บน Render

1. เข้า [render.com](https://render.com/) → สมัครสมาชิก (ใช้ GitHub login ได้)
2. กด **New** → **Web Service**
3. เชื่อมต่อ GitHub repo ที่เพิ่ง push ขึ้นไป
4. ตั้งค่าดังนี้:

| การตั้งค่า | ค่า |
|---|---|
| **Name** | discord-music-bot |
| **Runtime** | Docker |
| **Instance Type** | Free |

5. เพิ่ม **Environment Variable**:
   - Key: `DISCORD_TOKEN`
   - Value: Token ของบอท (คัดลอกจาก `.env`)

6. กด **Create Web Service** → รอ Deploy

### ขั้นตอนที่ 3: ตั้ง UptimeRobot ไม่ให้ Render หลับ

1. เข้า [uptimerobot.com](https://uptimerobot.com/) → สมัครสมาชิกฟรี
2. กด **Add New Monitor**
3. ตั้งค่า:

| การตั้งค่า | ค่า |
|---|---|
| **Monitor Type** | HTTP(s) |
| **Friendly Name** | Discord Music Bot |
| **URL** | `https://ชื่อ-service.onrender.com` |
| **Monitoring Interval** | 5 minutes |

4. กด **Create Monitor**

> UptimeRobot จะ ping บอททุก 5 นาที ทำให้ Render ไม่เข้าโหมดหลับ (ฟรีรองรับ 50 monitors)

### ✅ เสร็จสิ้น!

บอทจะรัน 24/7 บน Render โดยไม่ต้องเปิดคอมเครื่องตัวเองแล้วครับ 🎉
