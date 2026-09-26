"""Load the Amazon module once, triggering and persisting browser OAuth."""

import sys
from pathlib import Path


# Executing ``python scripts/amazon_login.py`` makes Python use /app/scripts as
# sys.path[0]. Add the repository root explicitly so the Orpheus package and
# local modules remain importable inside Docker.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from orpheus.core import Orpheus


orpheus = Orpheus()
orpheus.load_module("amazonmusic")
print("AMAZON_LOGIN_SUCCESS", flush=True)
