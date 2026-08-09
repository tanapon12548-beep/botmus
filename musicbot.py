import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
from dotenv import load_dotenv 
from collections import deque
from aiohttp import web

load_dotenv()

# ตั้งค่า PATH สำหรับ Deno บน Render (ต้องตั้งก่อน yt-dlp ทำงาน)
deno_install = os.path.join(os.path.expanduser('~'), '.deno')
if os.path.exists(deno_install):
    os.environ['PATH'] = os.path.join(deno_install, 'bin') + os.pathsep + os.environ.get('PATH', '')

# ตั้งค่า Intents ให้บอทอ่านข้อความได้
intents = discord.Intents.default()
intents.message_content = True

# ตั้งค่า Prefix เป็น ! (เช่น !play, !stop)
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่าสำหรับ yt-dlp และ FFmpeg เพื่อสตรีมเสียง
# 1. เช็ค YOUTUBE_COOKIES จาก Environment Variable (สำหรับ Render)
_env_cookies = os.getenv('YOUTUBE_COOKIES')
_cookies_path = None

if _env_cookies:
    _tmp_cookies = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies_env.txt')
    try:
        with open(_tmp_cookies, 'w', encoding='utf-8') as f:
            f.write(_env_cookies)
        _cookies_path = _tmp_cookies
    except Exception as e:
        print(f"Error writing YOUTUBE_COOKIES env: {e}")

if not _cookies_path:
    _cookies_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
    _cookies_render = '/etc/secrets/cookies.txt'
    if os.path.isfile(_cookies_local):
        _cookies_path = _cookies_local
    elif os.path.isfile(_cookies_render):
        _cookies_path = _cookies_render

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'source_address': '0.0.0.0',
    'remote_components': ['ejs:github'],
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
}
# เพิ่ม cookies ถ้ามีไฟล์
if _cookies_path:
    print(f"ใช้งาน Cookies จาก: {_cookies_path}")
    ytdl_format_options['cookiefile'] = _cookies_path
else:
    print("คำเตือน: ไม่พบไฟล์ Cookies! บน Render จำเป็นต้องตั้งค่า YOUTUBE_COOKIES หรือ Secret File")

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# หา FFmpeg — ลองจาก bin/ ก่อน (สำหรับ Render) ถ้าไม่มีใช้ system PATH
_ffmpeg_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'ffmpeg')
FFMPEG_PATH = _ffmpeg_local if os.path.isfile(_ffmpeg_local) else 'ffmpeg'

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# --- ระบบคิวเพลง (ไม่จำกัดจำนวน) ---
# เก็บคิวแยกตาม guild (เซิร์ฟเวอร์)
song_queues = {}  # guild_id -> deque of {'url': ..., 'title': ...}

def get_queue(guild_id):
    """ดึงคิวของเซิร์ฟเวอร์ ถ้ายังไม่มีก็สร้างใหม่"""
    if guild_id not in song_queues:
        song_queues[guild_id] = deque()
    return song_queues[guild_id]

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        # ดึงข้อมูลเพลงแบบ stream ไม่ดาวน์โหลดลงเครื่อง
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

async def play_next(ctx):
    """เล่นเพลงถัดไปในคิว"""
    queue = get_queue(ctx.guild.id)
    voice_client = ctx.voice_client

    if not queue or not voice_client:
        return

    next_song = queue.popleft()
    try:
        player = await YTDLSource.from_url(next_song['url'], loop=bot.loop)

        def after_playing(error):
            if error:
                print(f'มีข้อผิดพลาด: {error}')
            # เรียกเล่นเพลงถัดไปใน event loop
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        voice_client.play(player, after=after_playing)
        await ctx.send(f'🎵 กำลังเล่น: **{player.title}**')
    except Exception as e:
        await ctx.send(f"เกิดข้อผิดพลาดในการดึงข้อมูลเพลง: {e}")
        # ถ้า error ให้ลองเล่นเพลงถัดไป
        await play_next(ctx)

# --- Keep-Alive Web Server สำหรับ UptimeRobot ---
async def health_check(request):
    return web.Response(text="บอทยังทำงานอยู่! 🎵")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f'Web server ทำงานบนพอร์ต {port}')

@bot.event
async def on_ready():
    print(f'ล็อกอินสำเร็จในชื่อ {bot.user}')
    # เริ่ม web server เพื่อให้ UptimeRobot ping ได้
    await start_web_server()

@bot.command(name='play', aliases=['p'], help='เล่นเพลงจากชื่อเพลงหรือ URL (ถ้ากำลังเล่นอยู่จะเพิ่มเข้าคิว)')
async def play(ctx, *, query):
    # ตรวจสอบว่าผู้ใช้รันคำสั่งอยู่ใน Voice Channel หรือไม่
    if not ctx.message.author.voice:
        await ctx.send("คุณต้องเข้า Voice Channel ก่อนครับ!")
        return

    channel = ctx.message.author.voice.channel
    voice_client = ctx.voice_client

    # ถ้าบอทยังไม่เข้าห้อง ให้เข้าห้อง
    if voice_client is None:
        voice_client = await channel.connect(self_deaf=True, timeout=60.0)
    else:
        await voice_client.move_to(channel)

    queue = get_queue(ctx.guild.id)

    # ถ้ากำลังเล่นอยู่ → เพิ่มเข้าคิว
    if voice_client.is_playing() or voice_client.is_paused():

        async with ctx.typing():
            try:
                # ดึงแค่ชื่อเพลง ไม่ต้องสร้าง source ตอนนี้
                data = await bot.loop.run_in_executor(
                    None, lambda: ytdl.extract_info(query, download=False)
                )
                if 'entries' in data:
                    data = data['entries'][0]
                title = data.get('title', 'ไม่ทราบชื่อ')
                queue.append({'url': query, 'title': title})
                await ctx.send(f'📋 เพิ่มเข้าคิว #{len(queue)}: **{title}**')
            except Exception as e:
                await ctx.send(f"เกิดข้อผิดพลาดในการดึงข้อมูลเพลง: {e}")
        return

    # ถ้าไม่ได้เล่นอยู่ → เล่นเลย
    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(query, loop=bot.loop)

            def after_playing(error):
                if error:
                    print(f'มีข้อผิดพลาด: {error}')
                asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

            voice_client.play(player, after=after_playing)
            await ctx.send(f'🎵 กำลังเล่น: **{player.title}**')
        except Exception as e:
            await ctx.send(f"เกิดข้อผิดพลาดในการดึงข้อมูลเพลง: {e}")

@bot.command(name='skip', aliases=['s', 'sk'], help='ข้ามเพลงปัจจุบัน')
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()  # จะ trigger after callback → เล่นเพลงถัดไปอัตโนมัติ
        await ctx.send("⏭️ ข้ามเพลง!")
    else:
        await ctx.send("ไม่มีเพลงที่กำลังเล่นอยู่ครับ")

@bot.command(name='jump', aliases=['j'], help='เลือกเพลงในคิวมาเล่นเลย เช่น !j 3')
async def jump_to(ctx, index: int):
    queue = get_queue(ctx.guild.id)
    voice_client = ctx.voice_client

    if not queue:
        await ctx.send("📋 คิวว่างเปล่า ไม่มีเพลงให้เลือกครับ")
        return

    if index < 1 or index > len(queue):
        await ctx.send(f"❌ กรุณาระบุหมายเลข 1-{len(queue)} ครับ (ดูคิวด้วย `!queue`)")
        return

    # ดึงเพลงที่เลือกมาไว้หัวคิว โดยเพลงอื่นยังอยู่
    selected = queue[index - 1]
    del queue[index - 1]
    queue.appendleft(selected)

    await ctx.send(f"⏩ ข้ามไปเล่น: **{selected['title']}**")

    # หยุดเพลงปัจจุบัน → after callback จะเล่นเพลงหัวคิว (ที่เราเลือก) อัตโนมัติ
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()

@bot.command(name='queue', aliases=['q'], help='ดูรายการเพลงในคิว')
async def show_queue(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await ctx.send("📋 คิวว่างเปล่า")
        return

    queue_list = ""
    for i, song in enumerate(queue, 1):
        queue_list += f"**{i}.** {song['title']}\n"

    await ctx.send(f"📋 **คิวเพลง ({len(queue)} เพลง):**\n{queue_list}")

@bot.command(name='clear', aliases=['cl'], help='ล้างคิวเพลงทั้งหมด')
async def clear_queue(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()
    await ctx.send("🗑️ ล้างคิวเพลงแล้ว!")

@bot.command(name='remove', aliases=['rm'], help='ลบเพลงออกจากคิว เช่น !rm 2')
async def remove_from_queue(ctx, index: int):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await ctx.send("📋 คิวว่างเปล่า ไม่มีอะไรให้ลบครับ")
        return

    if index < 1 or index > len(queue):
        await ctx.send(f"❌ กรุณาระบุหมายเลข 1-{len(queue)} ครับ (ดูคิวด้วย `!queue`)")
        return

    removed = queue[index - 1]
    del queue[index - 1]
    await ctx.send(f"🗑️ ลบเพลง #{index}: **{removed['title']}** ออกจากคิวแล้ว!")

@bot.command(name='stop', aliases=['dc', 'leave'], help='หยุดเพลงและสั่งบอทออก')
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        # ล้างคิวก่อนออก
        queue = get_queue(ctx.guild.id)
        queue.clear()
        await voice_client.disconnect()
        await ctx.send("🛑 ออกจากห้องและหยุดเล่นเพลงแล้ว")
    else:
        await ctx.send("บอทไม่ได้อยู่ใน Voice Channel ครับ")

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)