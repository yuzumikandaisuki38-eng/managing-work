#!/usr/bin/env python3
"""Generate an original abstract-art CM for ツイテル鑑定所.

The image and music are synthesized locally, so the generated assets do not
depend on stock-media licenses. FFmpeg is optional: without it, PNG and WAV
files are still produced.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import wave
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


MESSAGES = (
    ("金運", "小さな見直しが大きな実りに。財布と予定を整えると吉。"),
    ("健康運", "無理を手放して、深呼吸をひとつ。体をいたわる選択が運気を育てます。"),
    ("金運", "学びや道具への投資が未来につながる日。焦らず一歩ずつ。"),
    ("健康運", "朝の水分補給と軽いストレッチで、心身の巡りを整えましょう。"),
)


def daily_message(day: dt.date) -> tuple[str, str]:
    return MESSAGES[day.toordinal() % len(MESSAGES)]


def japanese_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    print("[WARNING] Japanese font not found; text may not render correctly.")
    return ImageFont.load_default()


def generate_art(path: Path, seed: int, size: tuple[int, int], category: str, message: str) -> None:
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

    pastel = LinearSegmentedColormap.from_list(
        "tsuiteru_pastel",
        [
            "#f8e8e8",
            "#f5d6d8",
            "#d9d1eb",
            "#c8dff0",
            "#cce8dc",
            "#f5e3b8",
        ],
    )
    fig, ax = plt.subplots(figsize=(9, 16), dpi=100)
    ax.imshow(
        image,
        cmap=pastel,
        origin="lower",
        interpolation="bicubic",
        vmin=-2.2,
        vmax=2.2,
    )
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path, dpi=100, facecolor="#f8eee8")
    plt.close(fig)

    art = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", art.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = art.size
    title_font = japanese_font(54)
    category_font = japanese_font(38)
    body_font = japanese_font(27)
    small_font = japanese_font(24)
    draw.rounded_rectangle(
        (42, 48, width - 42, 170),
        radius=28,
        fill=(12, 7, 30, 170),
        outline=(242, 228, 183, 190),
        width=2,
    )
    draw.text((width // 2, 108), "ツイテル鑑定所", font=title_font,
              fill=(242, 228, 183, 255), anchor="mm")
    panel_top = height - 360
    draw.rounded_rectangle(
        (42, panel_top, width - 42, height - 48),
        radius=28,
        fill=(12, 7, 30, 195),
        outline=(242, 228, 183, 180),
        width=2,
    )
    draw.text((width // 2, panel_top + 58), category, font=category_font,
              fill=(255, 226, 148, 255), anchor="mm")
    draw.text((width // 2, panel_top + 125), message, font=body_font,
              fill=(255, 255, 255, 255), anchor="mm", align="center",
              spacing=10)
    draw.text((width // 2, height - 82), "12月オープン予定｜個人鑑定受付中", font=small_font,
              fill=(225, 211, 235, 255), anchor="mm")
    Image.alpha_composite(art, overlay).convert("RGB").save(path, quality=95)


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
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-loop", "1", "-i", str(image), "-i", str(music),
        "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p",
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
    generate_art(image, seed, (720, 1280), category, message)
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
