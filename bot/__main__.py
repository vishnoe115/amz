import asyncio
import html
import os
import re
import shutil
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from modules.amazonmusic.interface import ModuleInterface


APP_ROOT = Path("/app")
CONFIG_DIR = APP_ROOT / "config"
DOWNLOAD_DIR = APP_ROOT / "downloads"
LOGIN_STORAGE = CONFIG_DIR / "loginstorage.bin"
AMAZON_URL_RE = re.compile(
    r"https?://(?:music\.)?amazon\.[a-z.]+/[^\s]+", re.IGNORECASE
)
OAUTH_URL_RE = re.compile(r"https://[^\s]+(?:openid|oauth)[^\s]+", re.IGNORECASE)
AUDIO_SUFFIXES = {".flac", ".m4a", ".mp3", ".wav", ".ogg", ".opus"}


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def admin_ids() -> set[int]:
    values = re.split(r"[\s,]+", os.environ.get("ADMINS", ""))
    return {int(value) for value in values if value.strip().lstrip("-").isdigit()}


API_ID = int(required_env("API_ID"))
API_HASH = required_env("API_HASH")
BOT_TOKEN = required_env("BOT_TOKEN")
ADMINS = admin_ids()
DOWNLOAD_TIMEOUT = max(60, int(os.environ.get("DOWNLOAD_TIMEOUT", "7200")))

app = Client(
    "amazon_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir=str(CONFIG_DIR),
)
download_lock = asyncio.Lock()
login_lock = asyncio.Lock()
pending_login: dict[int, asyncio.subprocess.Process] = {}


def is_logged_in() -> bool:
    try:
        return ModuleInterface.has_cached_credentials(str(LOGIN_STORAGE))
    except Exception:
        return False


async def read_login_url(process: asyncio.subprocess.Process) -> tuple[str | None, str]:
    captured: list[str] = []
    while True:
        line = await asyncio.wait_for(process.stdout.readline(), timeout=180)
        if not line:
            return None, "".join(captured)
        text = line.decode("utf-8", errors="replace")
        captured.append(text)
        match = OAUTH_URL_RE.search(text)
        if match:
            return match.group(0), "".join(captured)


@app.on_message(filters.command("start"))
async def start_handler(_: Client, message: Message):
    status = "✅ Login Amazon tersedia" if is_logged_in() else "❌ Belum login Amazon"
    admin_help = "\n\nAdmin: gunakan /amazon_login untuk login." if message.from_user and message.from_user.id in ADMINS else ""
    await message.reply_text(
        "<b>Amazon Music Test Bot</b>\n\n"
        f"Status: {status}\n"
        "Kirim link track, album, atau playlist Amazon Music untuk menguji download."
        f"{admin_help}",
        parse_mode=ParseMode.HTML,
    )


@app.on_message(filters.command("amazon_status"))
async def status_handler(_: Client, message: Message):
    await message.reply_text(
        "✅ Session Amazon tersedia." if is_logged_in() else "❌ Session Amazon belum tersedia."
    )


@app.on_message(filters.command("amazon_login") & filters.private)
async def login_handler(_: Client, message: Message):
    if not message.from_user or message.from_user.id not in ADMINS:
        await message.reply_text("Perintah ini hanya untuk admin bot.")
        return
    if login_lock.locked():
        await message.reply_text("Proses login Amazon lain masih berjalan.")
        return

    await login_lock.acquire()
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            "python3", "-u", "scripts/amazon_login.py",
            cwd=str(APP_ROOT),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        oauth_url, output = await read_login_url(process)
        if not oauth_url:
            await process.wait()
            if "AMAZON_LOGIN_SUCCESS" in output or is_logged_in():
                await message.reply_text("✅ Amazon Music sudah login dan session masih aktif.")
            else:
                await message.reply_text(
                    "❌ Gagal memulai login Amazon.\n\n"
                    f"<code>{html.escape(output[-1500:])}</code>",
                    parse_mode=ParseMode.HTML,
                )
            login_lock.release()
            return

        pending_login[message.from_user.id] = process
        await message.reply_text(
            "<b>Login Amazon Music</b>\n\n"
            "1. Tekan tombol di bawah dan login pada situs Amazon.\n"
            "2. Selesaikan CAPTCHA/MFA jika diminta.\n"
            "3. Salin <b>seluruh URL terakhir</b> dari address bar.\n"
            "4. Kirim URL tersebut ke chat ini.\n\n"
            "Jangan kirim password Amazon ke bot.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔐 Login Amazon", url=oauth_url)]]
            ),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        if process and process.returncode is None:
            process.kill()
            await process.wait()
        if login_lock.locked():
            login_lock.release()
        await message.reply_text(f"❌ Gagal memulai login: <code>{html.escape(str(exc))}</code>", parse_mode=ParseMode.HTML)


@app.on_message(filters.private & filters.text, group=-10)
async def login_callback_handler(_: Client, message: Message):
    if not message.from_user or message.from_user.id not in pending_login:
        return
    process = pending_login.pop(message.from_user.id)
    try:
        callback_url = (message.text or "").strip()
        if not callback_url.startswith("http"):
            pending_login[message.from_user.id] = process
            await message.reply_text("Kirim seluruh URL callback Amazon, dimulai dengan http/https.")
            return
        process.stdin.write((callback_url + "\n").encode())
        await process.stdin.drain()
        output, _ = await asyncio.wait_for(process.communicate(), timeout=300)
        result = output.decode("utf-8", errors="replace")
        if process.returncode == 0 and ("AMAZON_LOGIN_SUCCESS" in result or is_logged_in()):
            await message.reply_text("✅ Login Amazon Music berhasil. Session sudah disimpan dan bot siap digunakan.")
        else:
            await message.reply_text(
                "❌ Login Amazon gagal. Jalankan /amazon_login untuk mencoba kembali.\n\n"
                f"<code>{html.escape(result[-1500:])}</code>",
                parse_mode=ParseMode.HTML,
            )
    except Exception as exc:
        if process.returncode is None:
            process.kill()
            await process.wait()
        await message.reply_text(f"❌ Login Amazon gagal: <code>{html.escape(str(exc))}</code>", parse_mode=ParseMode.HTML)
    finally:
        if login_lock.locked():
            login_lock.release()
        message.stop_propagation()


@app.on_message(filters.text & filters.regex(AMAZON_URL_RE))
async def download_handler(client: Client, message: Message):
    match = AMAZON_URL_RE.search(message.text or "")
    if not match:
        return
    if not is_logged_in():
        await message.reply_text("❌ Amazon Music belum login. Admin harus menjalankan /amazon_login terlebih dahulu.")
        return
    if download_lock.locked():
        await message.reply_text("⏳ Bot sedang mengerjakan download lain. Silakan coba kembali setelah selesai.")
        return

    link = match.group(0)
    task_id = f"{message.chat.id}_{message.id}"
    task_dir = DOWNLOAD_DIR / task_id
    status = await message.reply_text("⏳ Memulai download Amazon Music...")

    async with download_lock:
        try:
            task_dir.mkdir(parents=True, exist_ok=True)
            process = await asyncio.create_subprocess_exec(
                "python3", "-u", "orpheus.py", "-o", str(task_dir), link,
                cwd=str(APP_ROOT),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            output, _ = await asyncio.wait_for(process.communicate(), timeout=DOWNLOAD_TIMEOUT)
            log = output.decode("utf-8", errors="replace")
            files = sorted(
                path for path in task_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
            )
            if process.returncode != 0 or not files:
                reason = log[-1800:] or "Tidak ada file audio yang dihasilkan."
                await status.edit_text(
                    "❌ Download Amazon Music gagal.\n\n"
                    f"<code>{html.escape(reason)}</code>",
                    parse_mode=ParseMode.HTML,
                )
                return

            await status.edit_text(f"⬆️ Download selesai. Mengunggah 0/{len(files)} file...")
            for index, path in enumerate(files, start=1):
                await client.send_audio(message.chat.id, str(path), caption=f"Amazon Music • {index}/{len(files)}")
                await status.edit_text(f"⬆️ Mengunggah {index}/{len(files)} file...")
            await status.edit_text(f"✅ Selesai. {len(files)} file berhasil dikirim.")
        except asyncio.TimeoutError:
            if 'process' in locals() and process.returncode is None:
                process.kill()
                await process.wait()
            await status.edit_text("❌ Download dihentikan karena melewati batas waktu.")
        except Exception as exc:
            await status.edit_text(f"❌ Error: <code>{html.escape(str(exc))}</code>", parse_mode=ParseMode.HTML)
        finally:
            shutil.rmtree(task_dir, ignore_errors=True)


app.run()
