#!/usr/bin/env python3
"""Local-only server for generating reviewable CM assets from the landing page."""

from __future__ import annotations

import datetime as dt
import json
import mimetypes
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "cm_generator" / "generate_cm.py"
OUTPUT_DIR = ROOT / "generated"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/generate":
            self._json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length > 1024 * 16:
            self._json(413, {"error": "Request is too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            day = dt.date.fromisoformat(str(payload.get("date", "")))
        except (ValueError, TypeError, json.JSONDecodeError):
            self._json(400, {"error": "date must be YYYY-MM-DD"})
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(GENERATOR),
            "--date",
            day.isoformat(),
            "--output-dir",
            str(OUTPUT_DIR),
        ]
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self._json(504, {"error": "Generation timed out"})
            return

        if result.returncode != 0:
            self._json(500, {"error": "Generation failed", "details": result.stderr[-2000:]})
            return

        stem = f"tsuiteru_{day.isoformat()}"
        files = [
            f"/generated/{stem}.png",
            f"/generated/{stem}.wav",
        ]
        video = OUTPUT_DIR / f"{stem}.mp4"
        if video.exists():
            files.append(f"/generated/{stem}.mp4")
        self._json(200, {"date": day.isoformat(), "files": files, "log": result.stdout[-2000:]})

def main() -> None:
    port = 8000
    print(f"Serving {ROOT} at http://127.0.0.1:{port}")
    print("Review generated assets before any publication.")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
