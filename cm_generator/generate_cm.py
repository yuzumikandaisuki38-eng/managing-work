#!/usr/bin/env python3
"""Generate an original abstract-art CM for ツイテル鑑定所.

The image and music are synthesized locally, so the generated assets do not
depend on stock-media licenses. FFmpeg is optional: without it, PNG and WAV
files are still produced.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import subprocess
import wave
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps


CM_SUBTITLE = "心と運気に寄り添う個人鑑定"
CM_OPENING = "12月オープン予定"
CM_RESERVATION = "オープン前から個人鑑定受付中"
CM_RECRUITMENT = "大阪市まで通える占い師さんを募集中"
CM_TITLE = "ツイテル鑑定所"
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


def three_line_message(message: str) -> str:
    """Split the daily message into three balanced Japanese lines."""
    if len(message) < 3:
        return message

    def split_at(text: str, target: int) -> int:
        target = max(1, min(len(text) - 1, target))
        candidates = [
            index + 1
            for index, character in enumerate(text)
            if character in "、。！？" and 1 <= index + 1 < len(text)
        ]
        nearby = [index for index in candidates if abs(index - target) <= 8]
        return min(nearby or [target], key=lambda index: abs(index - target))

    first_target = len(message) // 3
    first_end = split_at(message, first_target)
    remaining = message[first_end:]
    second_target = len(remaining) // 2
    second_end = split_at(remaining, second_target)
    return f"{message[:first_end]}\n{remaining[:second_end]}\n{remaining[second_end:]}"


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
    title: str = CM_TITLE,
    subtitle: str = CM_SUBTITLE,
    opening: str = CM_OPENING,
    reservation: str = CM_RESERVATION,
    recruitment: str = CM_RECRUITMENT,
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
    width, height = art.size
    overlay = Image.new("RGBA", art.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_font = japanese_font(48)
    subtitle_font = japanese_font(29)
    message_font = japanese_font(24)
    footer_font = japanese_font(19)
    panel_top = int(height * 0.23)
    panel_bottom = int(height * 0.84)
    box_left, box_right = 48, width - 48
    box_fill = (12, 7, 30, 0)
    box_outline = (255, 224, 112, 150)

    def text_box(top: int, bottom: int) -> None:
        draw.rounded_rectangle(
            (box_left, top, box_right, bottom),
            radius=18,
            fill=box_fill,
            outline=box_outline,
            width=2,
        )

    # Seven balanced transparent boxes: heading, three message lines, and
    # three closing notices.
    text_box(panel_top, panel_top + 160)
    draw.text(
        (width // 2, panel_top + 62),
        title,
        font=title_font,
        fill=(255, 235, 92, 255),
        stroke_width=4,
        stroke_fill=(48, 21, 8, 240),
        anchor="mm",
    )
    draw.text(
        (width // 2, panel_top + 125),
        subtitle,
        font=subtitle_font,
        fill=(255, 244, 142, 255),
        stroke_width=3,
        stroke_fill=(48, 21, 8, 235),
        anchor="mm",
    )
    message_lines = three_line_message(message or CM_RESERVATION).splitlines()
    message_top = panel_top + 178
    for index, line in enumerate(message_lines):
        top = message_top + index * 58
        text_box(top, top + 48)
        draw.text(
            (width // 2, top + 24),
            line,
            font=message_font,
            fill=(255, 255, 232, 255),
            stroke_width=3,
            stroke_fill=(48, 21, 8, 235),
            anchor="mm",
        )
    footer_top = message_top + 3 * 58 + 8
    text_box(footer_top, footer_top + 42)
    text_box(footer_top + 50, footer_top + 92)
    text_box(footer_top + 100, min(panel_bottom, footer_top + 142))
    draw.text(
        (width // 2, footer_top + 21),
        opening,
        font=footer_font,
        fill=(255, 239, 120, 255),
        stroke_width=3,
        stroke_fill=(48, 21, 8, 235),
        anchor="mm",
    )
    draw.text(
        (width // 2, footer_top + 71),
        reservation,
        font=footer_font,
        fill=(255, 239, 120, 255),
        stroke_width=3,
        stroke_fill=(48, 21, 8, 235),
        anchor="mm",
    )
    draw.text(
        (width // 2, min(panel_bottom - 21, footer_top + 121)),
        recruitment,
        font=footer_font,
        fill=(255, 239, 120, 255),
        stroke_width=3,
        stroke_fill=(48, 21, 8, 235),
        anchor="mm",
    )
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


def generate_editable_svg(
    path: Path,
    background: Path | None,
    message: str,
    title: str = CM_TITLE,
    subtitle: str = CM_SUBTITLE,
    opening: str = CM_OPENING,
    reservation: str = CM_RESERVATION,
    recruitment: str = CM_RECRUITMENT,
) -> None:
    """Write a Canva-friendly SVG with a separate image and text elements."""
    if background is None or not background.exists():
        background = DEFAULT_BACKGROUND
    encoded = base64.b64encode(background.read_bytes()).decode("ascii")
    media_type = "image/png" if background.suffix.lower() == ".png" else (
        "image/webp" if background.suffix.lower() == ".webp" else "image/jpeg"
    )
    lines = three_line_message(message or CM_RESERVATION).splitlines()
    texts = [
        (360, 235, title, 48),
        (360, 298, subtitle, 29),
        (360, 430, lines[0], 24),
        (360, 488, lines[1], 24),
        (360, 546, lines[2], 24),
        (360, 650, opening, 19),
        (360, 700, reservation, 19),
        (360, 750, recruitment, 19),
    ]
    text_elements = "\n".join(
        f'  <text x="{x}" y="{y}" font-family="Hiragino Kaku Gothic ProN, sans-serif" '
        f'font-size="{size}" text-anchor="middle" fill="#fff06a" stroke="#301508" '
        f'stroke-width="3" paint-order="stroke">{html.escape(text)}</text>'
        for x, y, text, size in texts
    )
    path.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280" viewBox="0 0 720 1280">
  <title>{html.escape(title)}</title>
  <image href="data:{media_type};base64,{encoded}" x="0" y="0" width="720" height="1280" preserveAspectRatio="xMidYMid slice"/>
{text_elements}
</svg>
''',
        encoding="utf-8",
    )


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
    parser.add_argument("--title", default=CM_TITLE)
    parser.add_argument("--subtitle", default=CM_SUBTITLE)
    parser.add_argument("--opening", default=CM_OPENING)
    parser.add_argument("--reservation", default=CM_RESERVATION)
    parser.add_argument("--recruitment", default=CM_RECRUITMENT)
    parser.add_argument("--message", default=None, help="Override the daily message")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else args.date.toordinal()
    message = args.message if args.message is not None else daily_message(args.date)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"tsuiteru_{args.date.isoformat()}"
    image = args.output_dir / f"{stem}.png"
    music = args.output_dir / f"{stem}.wav"
    video = args.output_dir / f"{stem}.mp4"
    editable_svg = args.output_dir / f"{stem}_canva_editable.svg"
    generate_art(
        image,
        seed,
        (720, 1280),
        args.background,
        message,
        args.title,
        args.subtitle,
        args.opening,
        args.reservation,
        args.recruitment,
    )
    if DEFAULT_MUSIC.exists():
        music.write_bytes(DEFAULT_MUSIC.read_bytes())
    else:
        generate_music(music, seed)
    generate_video(image, music, video)
    generate_editable_svg(
        editable_svg,
        args.background,
        message,
        args.title,
        args.subtitle,
        args.opening,
        args.reservation,
        args.recruitment,
    )
    print(f"Generated: {image} and {music}")
    print(f"CM message: {message}")
    valid = validate_assets(image, music, video)
    print("Review required before any social posting or publication.")
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
