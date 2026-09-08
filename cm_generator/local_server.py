#!/usr/bin/env python3
"""Local-only server for generating reviewable CM assets from the landing page."""

from __future__ import annotations

import datetime as dt
import io
import json
import subprocess
import sys
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "cm_generator" / "generate_cm.py"
OUTPUT_DIR = ROOT / "generated"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        if self.path.startswith("/generated/"):
            file_path = Path(self.translate_path(self.path))
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", self.guess_type(str(file_path)) or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return io.BytesIO(content)
        return super().send_head()

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _build_bundle(self, stem: str, day: dt.date) -> str:
        bundle_name = f"{stem}.zip"
        bundle_path = OUTPUT_DIR / bundle_name
        archive_members = [OUTPUT_DIR / f"{stem}.png", OUTPUT_DIR / f"{stem}.wav"]
        video_path = OUTPUT_DIR / f"{stem}.mp4"
        if video_path.exists():
            archive_members.append(video_path)
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in archive_members:
                archive.write(file_path, arcname=file_path.name)
            readme = f"TSUITERU CM review bundle\nDate: {day.isoformat()}\nFiles are ready for manual review before publishing.\n"
            archive.writestr("README.txt", readme, compress_type=zipfile.ZIP_DEFLATED)
        return f"/generated/{bundle_name}"

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/generate":
            self._json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "Invalid Content-Length"})
            return
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
        bundle = self._build_bundle(stem, day)
        self._json(200, {"date": day.isoformat(), "files": files, "bundle": bundle, "log": result.stdout[-2000:]})

def main() -> None:
    port = 8000
    print(f"Serving {ROOT} at http://127.0.0.1:{port}")
    print("Review generated assets before any publication.")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
