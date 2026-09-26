"""Apply container-safe Amazon defaults without storing secrets in Git."""

import json
import os
from pathlib import Path


settings_path = Path("/app/config/settings.json")
if not settings_path.is_file():
    raise SystemExit("config/settings.json was not generated")

settings = json.loads(settings_path.read_text(encoding="utf-8"))
amazon = settings.setdefault("modules", {}).setdefault("amazonmusic", {})

wvd_path = os.environ.get("AMZ_WVD_PATH", "/run/secrets/amazon.wvd").strip()
country = os.environ.get("AMZ_COUNTRY", "US").strip().upper()

amazon["wvd_path"] = wvd_path
amazon["country"] = country
# Browser OAuth is used by the module; plaintext Amazon passwords are neither
# required nor written into settings.json.
amazon["email"] = ""
amazon["password"] = ""

settings_path.write_text(json.dumps(settings, indent=4), encoding="utf-8")
