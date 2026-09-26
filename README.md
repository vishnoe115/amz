# Amazon Music Telegram Test Bot

Telegram test bot built from OrpheusDL and the supplied Amazon Music module.
Amazon authentication uses the official browser OAuth page; Amazon email and
password are never stored in `config.env`.

> Use only with an Amazon Music subscription and Widevine device that you are
> authorized to use. Never commit or share `.wvd`, cookies, tokens, or
> `config/loginstorage.bin`.

## Configuration

```bash
git clone https://github.com/vishnoe115/amz.git
cd amz
cp config.env.example config.env
```

Edit `config.env`:

```env
BOT_TOKEN=123456:telegram_bot_token
API_ID=12345678
API_HASH=telegram_api_hash
ADMINS=123456789
BOT_USERNAME=your_bot_username
DATABASE_URL=postgresql://user:password@host:5432/database
AMZ_COUNTRY=US
DOWNLOAD_TIMEOUT=7200
```

Multiple admins may be separated with commas:

```env
ADMINS=123456789,987654321
```

Copy your legally provisioned Widevine device to the project root:

```bash
cp /path/to/your/device.wvd ./device.wvd
chmod 600 device.wvd config.env
```

The Docker configuration mounts `device.wvd` read-only. It is excluded from
Git and from the Docker build context.

## Start the bot

```bash
docker compose up -d --build
docker compose logs -f
```

Docker Compose v1:

```bash
docker-compose up -d --build
docker-compose logs -f
```

## Login Amazon Music

1. Open a private chat with the Telegram bot.
2. Send `/amazon_login` from a Telegram ID listed in `ADMINS`.
3. Press **Login Amazon**.
4. Sign in on Amazon and complete CAPTCHA/MFA if requested.
5. The last browser page may show an error; this is expected.
6. Copy the complete URL from the browser address bar.
7. Send that URL back to the bot's private chat.
8. Wait for `Login Amazon Music berhasil`.

The reusable session is stored in the mounted `config` directory as
`config/loginstorage.bin` and backed up to PostgreSQL. At startup, the bot
restores the database copy before Orpheus initializes. Check the session with
`/amazon_status`.

The database account must be allowed to create and update the table
`amz_runtime_state`. The session is stored in a `BYTEA` column; keep the
database private because the session contains reusable Amazon credentials.

## Test a download

Send a track, album, or playlist link such as:

```text
https://music.amazon.com/albums/ALBUM_ID
```

Downloads run one task at a time. Audio files are uploaded to the requesting
Telegram chat and temporary files are removed afterward.

## Commands

- `/start` — bot and login status
- `/amazon_login` — begin Amazon browser login; admin and private chat only
- `/amazon_status` — check whether a cached Amazon session exists

## Included runtime

- OrpheusDL core
- Supplied Amazon Music module
- Pyrogram Telegram frontend
- Shaka Packager `v3.9.3`
- Bento4 `mp4decrypt` `1.6.0-641`
- FFmpeg

The original credential-object debug statement was removed because it could
expose access tokens, cookies, and the device signing key. The supplied Amazon
module did not include an explicit license file; confirm redistribution rights
with its author before sharing this repository further.
