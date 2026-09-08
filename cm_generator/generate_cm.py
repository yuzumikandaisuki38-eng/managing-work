#!/usr/bin/env python3
"""Generate an original abstract-art CM for ツイテル鑑定所.

The image and music are synthesized locally, so the generated assets do not
depend on stock-media licenses. FFmpeg is optional: without it, PNG and WAV
files are still produced.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import wave
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


MESSAGES = (
    ("金運", "小さな見直しが大きな実りに。財布と予定を整えると吉。"),
    ("健康運", "無理を手放して、深呼吸をひとつ。体をいたわる選択が運気を育てます。"),
    ("金運", "学びや道具への投資が未来につながる日。焦らず一歩ずつ。"),
    ("健康運", "朝の水分補給と軽いストレッチで、心身の巡りを整えましょう。"),
)


def daily_message(day: dt.date) -> tuple[str, str]:
    return MESSAGES[day.toordinal() % len(MESSAGES)]


def generate_art(path: Path, seed: int, size: tuple[int, int]) -> None:
    rng = np.random.default_rng(seed)
    width, height = size
    x = np.linspace(-6, 6, width)
    y = np.linspace(-6, 6, height)
    X, Y = np.meshgrid(x, y)
    radius = np.hypot(X, Y)
    angle = np.arctan2(Y, X)
    flow = (
        np.sin(radius * 2.3 + np.sin(angle * 5) * 1.8)
        + 0.55 * np.cos(X * Y * 0.8)
        + 0.35 * np.sin(X * 1.7 - Y * 2.2)
    )
    noise = rng.normal(0, 0.08, (height, width))
    image = flow + noise

    fig, ax = plt.subplots(figsize=(9, 16), dpi=100)
    ax.imshow(image, cmap="magma", origin="lower", interpolation="bicubic")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path, dpi=100, facecolor="#120b2e")
    plt.close(fig)


def generate_music(path: Path, seed: int, seconds: int = 12, sample_rate: int = 44100) -> None:
    rng = np.random.default_rng(seed)
    t = np.arange(seconds * sample_rate) / sample_rate
    notes = np.array([220.0, 261.63, 329.63, 392.0])
    melody = sum(
        np.sin(2 * np.pi * notes[i % len(notes)] * t + rng.random() * 2 * np.pi)
        * np.exp(-((t % 3.0) - 1.5) ** 2 / 1.8)
        for i in range(len(notes))
    )
    pad = 0.35 * np.sin(2 * np.pi * 110.0 * t) + 0.2 * np.sin(2 * np.pi * 164.81 * t)
    fade = np.minimum(1, t * 3) * np.minimum(1, (seconds - t) * 3)
    audio = np.clip((melody * 0.12 + pad) * fade, -1, 1)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def generate_video(image: Path, music: Path, output: Path, message: str, category: str) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("FFmpeg not found; skipped MP4 (PNG and WAV were generated).")
        return
    drawtext = (
        "drawtext=text='ツイテル鑑定所':fontcolor=white:fontsize=52:"
        "x=(w-text_w)/2:y=90,"
        f"drawtext=text='{category}  {message}':fontcolor=white:fontsize=28:"
        "x=(w-text_w)/2:y=h-180"
    )
    command = [
        ffmpeg, "-y", "-loop", "1", "-i", str(image), "-i", str(music),
        "-t", "12", "-vf", drawtext, "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(output),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def validate_assets(image: Path, music: Path, video: Path) -> bool:
    issues = []
    if not image.exists() or image.stat().st_size <= 0:
        issues.append(f"Missing or empty image: {image}")
    if not music.exists() or music.stat().st_size <= 0:
        issues.append(f"Missing or empty music: {music}")
    if video.exists() and video.stat().st_size <= 0:
        issues.append(f"Empty video: {video}")

    if issues:
        for issue in issues:
            print(f"[VALIDATION] {issue}")
        return False

    print("[VALIDATION] PNG and WAV assets are present and non-empty.")
    if video.exists():
        print("[VALIDATION] MP4 is present and will be reviewed before publication.")
    else:
        print("[VALIDATION] MP4 was not generated because FFmpeg is unavailable; review of PNG/WAV is still required before publishing.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument("--output-dir", type=Path, default=Path("generated"))
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else args.date.toordinal()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    category, message = daily_message(args.date)
    stem = f"tsuiteru_{args.date.isoformat()}"
    image = args.output_dir / f"{stem}.png"
    music = args.output_dir / f"{stem}.wav"
    video = args.output_dir / f"{stem}.mp4"
    generate_art(image, seed, (720, 1280))
    generate_music(music, seed)
    generate_video(image, music, video, message, category)
    print(f"Generated: {image} and {music}")
    print(f"Daily message ({category}): {message}")
    valid = validate_assets(image, music, video)
    print("Review required before any social posting or publication.")
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
