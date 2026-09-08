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
import textwrap
import wave
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps


CM_SUBTITLE = "心と運気に寄り添う個人鑑定"
CM_BODY = "12月オープン予定｜個人鑑定受付中"
MESSAGE_OPENINGS = (
    "今日は",
    "今こそ",
    "この瞬間から",
    "あなたの毎日に",
    "心の向くままに",
    "軽やかな気持ちで",
    "新しい一歩を",
    "いつもの一日に",
    "そっと深呼吸して",
    "笑顔をひとつ添えて",
)
MESSAGE_ACTIONS = (
    "小さな発見を楽しむと",
    "心がときめく方へ進むと",
    "気になっていたことを始めると",
    "身近な人との会話を大切にすると",
    "いつもと違う道を選ぶと",
    "自分のペースを信じると",
    "うれしい予定をひとつ思い描くと",
    "好きなものに触れる時間をつくると",
    "新しい景色に目を向けると",
    "感謝の気持ちを言葉にすると",
)
MESSAGE_RESULTS = (
    "素敵なチャンスが見つかります。",
    "思いがけない発見に出会えます。",
    "心が弾む出来事が始まります。",
    "明日への楽しみが広がります。",
    "あなたらしい魅力が輝きます。",
    "うれしいご縁が近づいてきます。",
    "毎日に新しい彩りが生まれます。",
    "未来への扉がそっと開きます。",
    "心地よい変化を感じられます。",
    "ワクワクする予感に包まれます。",
)
MESSAGE_CLOSINGS = (
    "楽しむ気持ちを大切に。",
    "焦らず、軽やかに進みましょう。",
    "あなたの直感を信じてみてください。",
    "今日の幸せを見つけてみましょう。",
    "小さな一歩から始めてみましょう。",
    "笑顔の時間を過ごせますように。",
    "心に余白を持って過ごしましょう。",
    "うれしいことを自分に贈りましょう。",
    "新しい発見を迎えに行きましょう。",
    "今日も素敵な一日になりますように。",
)
DEFAULT_BACKGROUND = Path(__file__).resolve().parent.parent / "assets" / "cm_default_space.jpeg"
DEFAULT_MUSIC = Path(__file__).resolve().parent.parent / "assets" / "cm_bgm_cc0.wav"


def daily_message(day: dt.date) -> str:
    message_number = day.toordinal() % 10_000
    opening = MESSAGE_OPENINGS[message_number % 10]
    action = MESSAGE_ACTIONS[(message_number // 10) % 10]
    result = MESSAGE_RESULTS[(message_number // 100) % 10]
    closing = MESSAGE_CLOSINGS[(message_number // 1_000) % 10]
    return f"{opening}{action}{result}{closing}"


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


def generate_art(
    path: Path,
    seed: int,
    size: tuple[int, int],
    background: Path | None = None,
    message: str = "",
) -> None:
    rng = np.random.default_rng(seed)
    width, height = size
    selected_background = background or (DEFAULT_BACKGROUND if DEFAULT_BACKGROUND.exists() else None)
    if selected_background is not None:
        art = ImageOps.fit(
            Image.open(selected_background).convert("RGB"),
            (width, height),
            method=Image.Resampling.LANCZOS,
        ).convert("RGBA")
        art.save(path)
    else:
        x = np.linspace(-6, 6, width)
        y = np.linspace(-6, 6, height)
        X, Y = np.meshgrid(x, y)
        radius = np.hypot(X, Y)
        angle = np.arctan2(Y, X)
        flow = (
            0.9 * np.sin(X * 1.35 + Y * 2.65 + np.sin(Y * 1.7) * 1.2)
            + 0.55 * np.cos(X * 2.1 - Y * 0.75 + np.sin(X * 0.9) * 1.4)
            + 0.35 * np.sin(radius * 1.8 + angle * 1.7)
            + 0.22 * np.cos(X * 0.55 + Y * 3.4)
        )
        milky_way = np.exp(-((Y - 0.48 * np.sin(X * 0.7) - 0.7) ** 2) / 2.3)
        field = flow + milky_way * 0.45
        noise = rng.normal(0, 0.08, (height, width))
        image = field + noise

        pastel = LinearSegmentedColormap.from_list(
            "tsuiteru_pastel",
            ["#f8e8e8", "#f5d6d8", "#d9d1eb", "#c8dff0", "#cce8dc", "#f5e3b8"],
        )
        fig, ax = plt.subplots(figsize=(9, 16), dpi=100)
        ax.imshow(image, cmap=pastel, origin="lower", interpolation="bicubic", vmin=-2.2, vmax=2.2)
        ax.axis("off")
        fig.subplots_adjust(0, 0, 1, 1)
        fig.savefig(path, dpi=100, facecolor="#f8eee8")
        plt.close(fig)
        art = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", art.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = art.size
    title_font = japanese_font(48)
    category_font = japanese_font(30)
    body_font = japanese_font(25)
    small_font = japanese_font(22)
    center_top = int(height * 0.34)
    center_bottom = int(height * 0.68)
    draw.rounded_rectangle(
        (42, center_top, width - 42, center_bottom),
        radius=32,
        fill=(12, 7, 30, 205),
        outline=(242, 228, 183, 190),
        width=2,
    )
    draw.text((width // 2, center_top + 66), "ツイテル鑑定所", font=title_font,
              fill=(242, 228, 183, 255), anchor="mm")
    draw.text((width // 2, center_top + 132), CM_SUBTITLE, font=category_font,
              fill=(255, 226, 148, 255), anchor="mm")
    message_lines = "\n".join(textwrap.wrap(message or CM_BODY, width=18, break_long_words=False))
    draw.multiline_text(
        (width // 2, center_top + 215),
        message_lines,
        font=body_font,
        fill=(255, 255, 255, 255),
        anchor="mm",
        align="center",
        spacing=12,
    )
    draw.text((width // 2, center_bottom - 28), CM_BODY, font=small_font,
              fill=(225, 211, 235, 255), anchor="ms")
    Image.alpha_composite(art, overlay).convert("RGB").save(path, quality=95)

    # Add a deterministic star field after the soft background is rendered.
    art = Image.open(path).convert("RGBA")
    stars = Image.new("RGBA", art.size, (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(stars)
    star_rng = np.random.default_rng(seed + 17)
    star_count = 170
    for _ in range(star_count):
        sx = int(star_rng.uniform(35, width - 35))
        sy = int(star_rng.uniform(180, height - 390))
        band = np.exp(-((sy / height - 0.48) ** 2) / 0.08)
        if star_rng.random() > 0.25 + band * 0.6:
            continue
        radius = float(star_rng.choice([1.0, 1.2, 1.6, 2.2, 3.0], p=[.32, .28, .2, .14, .06]))
        alpha = int(star_rng.uniform(110, 235))
        color = (255, 250, 224, alpha) if star_rng.random() > 0.18 else (225, 235, 255, alpha)
        star_draw.ellipse((sx - radius, sy - radius, sx + radius, sy + radius), fill=color)
        if radius >= 2.2:
            star_draw.line((sx - radius * 2.5, sy, sx + radius * 2.5, sy), fill=color, width=1)
            star_draw.line((sx, sy - radius * 2.5, sx, sy + radius * 2.5), fill=color, width=1)
    Image.alpha_composite(art, stars).convert("RGB").save(path, quality=95)


def generate_music(path: Path, seed: int, seconds: int = 12, sample_rate: int = 44100) -> None:
    t = np.arange(seconds * sample_rate) / sample_rate
    # Original calm cafe/lounge-inspired harmony; this does not copy the
    # linked recording or any melody from it.
    chords = (
        (0.8, (261.63, 329.63, 392.0)),
        (3.8, (220.0, 261.63, 329.63)),
        (6.8, (246.94, 293.66, 369.99)),
        (9.8, (196.0, 246.94, 293.66)),
    )
    audio = np.zeros_like(t, dtype=float)
    for start, frequencies in chords:
        local = t - start
        active = local >= 0
        envelope = np.where(active, np.exp(-local / 1.9) * (1 - np.exp(-local / 0.09)), 0)
        for frequency in frequencies:
            audio += (
                np.sin(2 * np.pi * frequency * local)
                + 0.06 * np.sin(2 * np.pi * frequency * 2 * local)
            ) * envelope / len(frequencies)
    fade = np.minimum(1, t / 1.2) * np.minimum(1, (seconds - t) / 1.8)
    audio = np.clip(audio * 0.018 * fade, -0.08, 0.08)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def generate_video(image: Path, music: Path, output: Path) -> None:
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
    parser.add_argument("--background", type=Path, default=None, help="Use one of the bundled CM background images")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else args.date.toordinal()
    message = daily_message(args.date)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"tsuiteru_{args.date.isoformat()}"
    image = args.output_dir / f"{stem}.png"
    music = args.output_dir / f"{stem}.wav"
    video = args.output_dir / f"{stem}.mp4"
    generate_art(image, seed, (720, 1280), args.background, message)
    if DEFAULT_MUSIC.exists():
        music.write_bytes(DEFAULT_MUSIC.read_bytes())
    else:
        generate_music(music, seed)
    generate_video(image, music, video)
    print(f"Generated: {image} and {music}")
    print(f"CM message: {message}")
    valid = validate_assets(image, music, video)
    print("Review required before any social posting or publication.")
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
