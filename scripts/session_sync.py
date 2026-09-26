"""Restore or save the Amazon session between disk and PostgreSQL."""

import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from bot.session_store import restore_session_from_database, save_session_to_database


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "restore"
    try:
        if action == "restore":
            changed = restore_session_from_database()
            print("DATABASE : Amazon session restored" if changed else "DATABASE : No stored Amazon session")
        elif action == "save":
            changed = save_session_to_database()
            print("DATABASE : Amazon session saved" if changed else "DATABASE : No Amazon session to save")
        else:
            raise SystemExit("Usage: session_sync.py [restore|save]")
    except Exception as exc:
        # Keep the bot usable with its local volume during a temporary database
        # outage. A later successful login/download will retry the upsert.
        print(f"DATABASE : Amazon session sync failed: {exc}")


if __name__ == "__main__":
    main()
