"""Download a small Piper English voice model into models/piper/.

Usage:
    python scripts/download_piper_voice.py
"""

from __future__ import annotations

import os
import sys
import urllib.request

VOICE = "en_US-lessac-medium"
BASE = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    f"en/en_US/lessac/medium/{VOICE}"
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "models", "piper")


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in (".onnx", ".onnx.json"):
        url = BASE + ext
        dest = os.path.join(OUT_DIR, VOICE + ext)
        if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
            print(f"Already present: {dest}")
            continue
        print(f"Downloading {url} -> {dest}")
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as exc:
            print(f"FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"Saved {dest} ({os.path.getsize(dest)} bytes)")
    print("Set PIPER_MODEL_PATH to:")
    print(os.path.join(OUT_DIR, VOICE + ".onnx"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
