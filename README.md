# Orpheus Amazon Music test repository

Isolated Docker test build of OrpheusDL with the supplied Amazon Music module.
It uses Amazon's browser OAuth flow and keeps login storage, downloads, and the
Widevine device outside the Git repository.

> Use this only with an Amazon Music account and Widevine device that you are
> authorized to use. Do not commit or share your `.wvd`, cookies, tokens, or
> `config/loginstorage.bin`.

## Requirements

- Docker with the Compose plugin
- An active Amazon Music account
- A valid, legally provisioned `.wvd` file for your own device

## Quick start

```bash
git clone https://github.com/vishnoe115/amz.git
cd amz
cp .env.example .env
```

Place the device file at `./device.wvd`. If it is stored elsewhere, edit
`WVD_FILE` in `.env`. Set `AMZ_COUNTRY` to the two-letter storefront country of
the Amazon account.

Build the image:

```bash
docker compose build
```

Start a download with an Amazon Music URL:

```bash
docker compose run --rm amazon-music "https://music.amazon.com/albums/ALBUM_ID"
```

During the first run, the terminal prints an Amazon authorization URL:

1. Open that URL in a normal browser.
2. Sign in directly on Amazon and finish CAPTCHA/MFA when requested.
3. The final browser page may show an error; this is expected.
4. Copy the complete final URL from the address bar.
5. Paste it into the Docker terminal and press Enter.

The reusable Amazon session is stored locally in `config/loginstorage.bin`.
The next download normally will not require another login. Downloaded media is
written to `./downloads`.

## Other commands

Open a temporary shell for diagnostics:

```bash
docker compose run --rm --entrypoint /bin/sh amazon-music
```

Reset only the Amazon login session while keeping a recoverable backup:

```bash
mv config/loginstorage.bin config/loginstorage.bin.backup
```

Run another download afterward to perform browser login again.

## Security notes

- The original credential-object debug statement was removed because that
  object contains reusable tokens, cookies, and a device signing key.
- `.wvd`, session files, configuration, and downloads are excluded from Git and
  Docker build context.
- Do not publish Docker logs produced with debug mode enabled.
- This repository does not contain a `.wvd` file or Amazon credentials.

## Included components

- OrpheusDL core
- Supplied `amazonmusic` module
- Shaka Packager `v3.9.3`
- Bento4 `mp4decrypt` `1.6.0-641`
- FFmpeg from Debian

The supplied Amazon module did not include an explicit license file. Confirm
redistribution permission with its author before distributing this repository
to third parties.
