"""
Auto-loads your .env file so you never have to export keys by hand.

Every session does `import env` as its first line. That single import reads
the .env file sitting next to it and puts your keys into os.environ — so
`anthropic.Anthropic()` and `os.environ["BRAVE_SEARCH_API_KEY"]` just work.

You normally never need to touch this file. Just run:  python session1.py

(This is a tiny, readable version of what the python-dotenv library does.)
"""

import os
from pathlib import Path


def load_env(path: Path | None = None) -> None:
    env_path = path or Path(__file__).with_name(".env")

    if not env_path.exists():
        print(f"[!] No .env file found next to your sessions ({env_path.name}).")
        print("    Run:  cp .env.example .env   then add your API keys.")
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # setdefault: a key already exported in your shell wins over the file.
        os.environ.setdefault(key, value)


# Runs on import — this is what makes `import env` enough.
load_env()
