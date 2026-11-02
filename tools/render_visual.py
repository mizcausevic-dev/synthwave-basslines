"""Procedural raster artwork and ffmpeg media steps.

The painter is original and deterministic. It draws a neon night road: a cyan
horizon, an amber gate, and bass pulses with gaps for rests. The tall pulses
are octave peaks in amber. The palette is navy, cyan, and amber. It is an
illustration, not a photograph of a session or of performers.

DejaVu Sans Bold is used only to rasterize the disclosure into the film and the
poster. The font file is not shipped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def _put(pixels: bytearray, width: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if x < 0 or y < 0:
        return
    height = len(pixels) // (width * 3)
    if x >= width or y >= height:
        return
    index = (y * width + x) * 3
    pixels[index] = color[0]
    pixels[index + 1] = color[1]
    pixels[index + 2] = color[2]


def _line(pixels: bytearray, width: int, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for step in range(steps + 1):
        x = int(x0 + (x1 - x0) * step / steps)
        y = int(y0 + (y1 - y0) * step / steps)
        _put(pixels, width, x, y, color)


def paint(width: int, height: int, framing: str) -> bytes:
    square = framing == "square"
    horizon = int(height * (0.46 if square else 0.58))
    pixels = bytearray(width * height * 3)
    for y in range(height):
        if y <= horizon:
            shade = y / max(1, horizon)
            red = int(6 + 16 * shade)
            green = int(8 + 22 * shade)
            blue = int(22 + 46 * shade)
        else:
            shade = (y - horizon) / max(1, height - horizon)
            red = int(12 - 6 * shade)
            green = int(16 - 8 * shade)
            blue = int(36 - 16 * shade)
        row = y * width * 3
        for x in range(width):
            pixels[row + x * 3] = max(0, red)
            pixels[row + x * 3 + 1] = max(0, green)
            pixels[row + x * 3 + 2] = max(0, blue)
    vanish_x = width // 2
    for band in range(1, 8):
        y = horizon + int((height - horizon) * band / 8)
        fade = 90 + band * 12
        _line(pixels, width, 0, y, width - 1, y, (10, fade, fade))
    for spoke in range(-7, 8):
        foot = vanish_x + int(spoke * width / 9)
        _line(pixels, width, vanish_x, horizon, foot, height - 1, (18, 90, 110))
    _line(pixels, width, 0, horizon, width - 1, horizon, (46, 230, 214))
    gate_y = int(horizon * (0.72 if square else 0.62))
    _line(pixels, width, int(width * 0.18), gate_y, int(width * 0.82), gate_y, (255, 180, 84))
    levels = (
        (0.42, False), (0.62, False), (0.48, False), (0.0, False),
        (0.55, False), (0.95, True), (0.4, False), (0.0, False),
        (0.7, False), (0.5, False), (1.0, True), (0.0, False),
        (0.46, False), (0.66, False), (0.38, False), (0.88, True),
    )
    if square:
        levels = (
            (0.0, False), (0.5, False), (0.72, False), (0.0, False),
            (1.0, True), (0.44, False), (0.0, False), (0.8, True),
            (0.36, False), (0.58, False),
        )
    margin = int(width * (0.16 if square else 0.1))
    floor = int(height * (0.78 if square else 0.84))
    ceiling = int(height * (0.18 if square else 0.28))
    span = max(1, width - margin * 2)
    slot = span / len(levels)
    for index, (level, peak) in enumerate(levels):
        if level <= 0:
            continue
        x0 = int(margin + index * slot + slot * 0.22)
        x1 = int(margin + index * slot + slot * 0.78)
        y0 = int(floor - level * (floor - ceiling))
        for y in range(max(0, y0), min(height, floor)):
            mix = (y - y0) / max(1, floor - y0)
            if peak:
                color = (255, 150 + int(40 * mix), 64)
            else:
                color = (24, 170 + int(50 * (1 - mix)), 190)
            row = y * width * 3
            for x in range(max(0, x0), min(width, x1)):
                pixels[row + x * 3] = color[0]
                pixels[row + x * 3 + 1] = color[1]
                pixels[row + x * 3 + 2] = color[2]
    return bytes(pixels)

def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
