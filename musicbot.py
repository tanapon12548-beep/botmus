import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
from dotenv import load_dotenv 
from collections import deque
from aiohttp import web
import urllib.request
import re

# เอาโฟลเดอร์ bin ใส่เข้าไปใน PATH ของระบบ เพื่อให้เรียก ffmpeg และ deno ได้อัตโนมัติ
_bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
os.environ["PATH"] = _bin_dir + os.pathsep + os.environ.get("PATH", "")

load_dotenv()

# เพิ่ม bin/ ของโปรเจค (ที่มีทั้ง ffmpeg และ deno) เข้า PATH บนสุด
_project_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
if os.path.isdir(_project_bin):
    os.environ['PATH'] = _project_bin + os.pathsep + os.environ.get('PATH', '')

deno_install = os.path.join(os.path.expanduser('~'), '.deno')
if os.path.exists(deno_install):
    os.environ['PATH'] = os.path.join(deno_install, 'bin') + os.pathsep + os.environ.get('PATH', '')

# ตั้งค่า Intents ให้บอทอ่านข้อความได้
intents = discord.Intents.default()
intents.message_content = True

# ตั้งค่า Prefix เป็น ! (เช่น !play, !stop)
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่าสำหรับ yt-dlp และ FFmpeg เพื่อสตรีมเสียง
# 1. เช็คไฟล์ Cookies ตามลำดับความสำคัญ ( Render Secret File -> Local -> Environment Variable)
_cookies_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
_cookies_render = '/etc/secrets/cookies.txt'
_tmp_cookies = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies_env.txt')

_cookies_path = None

if os.path.isfile(_cookies_render):
    _cookies_path = _cookies_render
elif os.path.isfile(_cookies_local):
    _cookies_path = _cookies_local
elif os.getenv('YOUTUBE_COOKIES'):
    try:
        with open(_tmp_cookies, 'w', encoding='utf-8') as f:
            f.write(os.getenv('YOUTUBE_COOKIES'))
        _cookies_path = _tmp_cookies
    except Exception as e:
        print(f"Error writing YOUTUBE_COOKIES env: {e}")

class YTDLLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
    'nocheckcertificate': True,
    'source_address': '0.0.0.0',
    'remote_components': ['ejs:github'],
    'logger': YTDLLogger(),
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
}
# ให้ระบบค้นหา Deno จาก PATH อัตโนมัติ (ใส่ bin ใน PATH ไว้แล้ว)

# เพิ่ม cookies ถ้ามีไฟล์
if _cookies_path:
    print(f"[Cookies] Loaded from: {_cookies_path}")
    ytdl_format_options['cookiefile'] = _cookies_path
else:
    print("[Cookies Warning] No cookies file found!")

ffmpeg_options = {
    'options': '-vn -af "apad=pad_dur=3"'
}

# หา FFmpeg — ลองจาก imageio_ffmpeg ก่อน แล้ว bin/ แล้วค่อย system PATH
# ใช้ FFmpeg จากระบบโดยตรง (รับประกันความเสถียรบน Docker)
FFMPEG_PATH = 'ffmpeg'
print(f"[FFmpeg] Executable path: {FFMPEG_PATH}")

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# พักระบบด้วย SoundCloud สตรีมสำรองกรณี YouTube บล็อก IP
ytdl_sc = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'scsearch',
    'nocheckcertificate': True,
    'logger': YTDLLogger(),
})

import re

def clean_query_term(q):
    if q.startswith('ytsearch:'):
        q = q[9:]
    elif q.startswith('scsearch:'):
        q = q[9:]
    return q.strip()

def get_oembed_title(query):
    try:
        import urllib.request, json
        q = clean_query_term(query)
        target_url = q if q.startswith('http') else f"https://www.youtube.com/watch?v={q}"
        oembed_url = f"https://www.youtube.com/oembed?url={target_url}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode('utf-8'))
            title = data.get('title', '')
            clean_title = re.sub(r'[\(\[\{].*?[\)\]\}]', '', title)
            clean_title = clean_title.replace('Official Video', '').replace('Official Audio', '').strip()
            return clean_title if clean_title else title
    except Exception:
        return None

def extract_info_sync(query, download=False):
    try:
        return ytdl.extract_info(query, download=download)
    except Exception as e:
        err_msg = str(e)
        if any(keyword in err_msg.lower() for keyword in ["sign in to confirm", "too many requests", "429", "bot"]):
            clean_q = clean_query_term(query)
            print(f"[Fallback] YouTube Block Detected for: {clean_q}")
            
            # 1. พยายามหาชื่อเพลงจริงผ่าน oEmbed
            search_term = get_oembed_title(clean_q) or clean_q
            print(f"[Fallback] Resolved search term: {search_term}")
            
            # ตัดชื่อศิลปินหลังเครื่องหมาย - หรือ | ออกเพื่อให้ SoundCloud ค้นหาง่ายขึ้น
            short_term = search_term.split('-')[0].split('|')[0].strip()
            
            # 2. ค้นหาใน SoundCloud ด้วยชื่อที่ตัดแล้ว
            try:
                sc_data = ytdl_sc.extract_info(f"scsearch:{short_term}", download=download)
                if sc_data and 'entries' in sc_data and len(sc_data['entries']) > 0:
                    return sc_data
            except Exception as sc_err:
                print(f"[Fallback] SoundCloud search error: {sc_err}")
                
            # 3. ลองใช้คำค้นหาเต็มๆ
            if search_term != short_term:
                try:
                    sc_data2 = ytdl_sc.extract_info(f"scsearch:{search_term}", download=download)
                    if sc_data2 and 'entries' in sc_data2 and len(sc_data2['entries']) > 0:
                        return sc_data2
                except Exception:
                    pass
            
            # ถ้าหาใน SoundCloud ไม่เจอเลย ให้แจ้งผู้ใช้แบบเข้าใจง่าย
            raise Exception(f"⚠️ YouTube บล็อกลิงก์นี้ และบอทพยายามหาเพลง '{short_term}' ใน SoundCloud สำรองให้แล้วแต่ไม่เจอครับ แนะนำให้ลองพิมพ์ชื่อเพลงค้นหาเอง (เช่น !play {short_term})")
        
        # ถ้าไม่ใช่ error ของ bot block ให้โยน error ปกติ
        raise e

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
        self.filename = None

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        # ดาวน์โหลดไฟล์ลงเครื่องก่อนเล่น ป้องกันปัญหา FFmpeg Network Segfault บน Cloud
        data = await loop.run_in_executor(None, lambda: extract_info_sync(url, download=True))
        
        if 'entries' in data:
            if not data['entries']:
                raise Exception("ไม่พบเพลงที่ค้นหา กรุณาลองค้นด้วยชื่อเพลงอื่นครับ")
            data = data['entries'][0]

        # yt-dlp จะคืนค่า 'requested_downloads' หรือใช้ 'url' หากเป็นการดึงไฟล์
        filename = data.get('filepath') or data.get('requested_downloads', [{}])[0].get('filepath')
        if not filename:
            # กรณีหา filepath ไม่เจอ ให้ลองใช้ค่า ext ประกอบชื่อ
            filename = ytdl.prepare_filename(data)
            
        # ใช้ FFmpegPCMAudio เพื่อแก้ปัญหาเสียงกระตุกจาก Opus copy
        player = cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)
        player.filename = filename
        return player

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
                    None, lambda: extract_info_sync(query)
                )
                if 'entries' in data:
                    if not data['entries']:
                        await ctx.send("❌ ไม่พบเพลงที่ค้นหาครับ")
                        return
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
                
                # ลบไฟล์ที่ดาวน์โหลดมาเพื่อประหยัดพื้นที่
                try:
                    if hasattr(player, 'source') and hasattr(player.source, 'original') and getattr(player.source.original, '_process', None) is None:
                        # ถ้า process ของ ffmpeg เคลียร์แล้ว ลบได้เลย
                        pass
                    if os.path.exists(player.filename):
                        os.remove(player.filename)
                except Exception as del_e:
                    print(f"ลบไฟล์ไม่สำเร็จ: {del_e}")
                    
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