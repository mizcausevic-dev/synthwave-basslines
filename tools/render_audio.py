"""Repo-owned preview synthesizer.

This is not a General MIDI soundfont and not a mix engine. It renders the
canonical notes for the preview arrangement with a filtered saw bass pulse
and a quiet triangle pad for the harmonic reference. Sample positions are
absolute:

    sample = floor(seconds * sample_rate + 0.5)

seconds = tick / 960 * encoded_microseconds_per_quarter / 1_000_000.
Intervals are not accumulated. Sample peak is not true peak and is not LUFS.
"""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

SR = 44100
RENDERER_VERSION = "simple-synth-1.0.0"


def tick_to_sample(tick: int, tempo_us: int, sample_rate: int = SR) -> int:
    seconds = (tick / 960) * (tempo_us / 1_000_000)
    return int(math.floor(seconds * sample_rate + 0.5))


def container_seconds(container_ticks: int, tempo_us: int) -> float:
    return (container_ticks / 960) * (tempo_us / 1_000_000)


def _midi_freq(pitch: int) -> float:
    return 440.0 * (2.0 ** ((pitch - 69) / 12.0))


def render_preview(parts: list[dict], tempo_us: int, container_ticks: int, wav_path: Path) -> dict:
    total = tick_to_sample(container_ticks, tempo_us)
    mix = array("i", [0]) * total

    def add_bass(note: dict) -> None:
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        low = 0.0
        amp = (note["velocity"] / 127.0) * 14000.0
        span = max(1, end - start)
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            saw = 2.0 * phase - 1.0
            low += 0.18 * (saw - low)
            t = (index - start) / SR
            remain = (end - index) / SR
            decay = 6.5 if span < int(0.35 * SR) else 0.65
            env = math.exp(-decay * t)
            if t < 0.004:
                env *= t / 0.004
            if remain < 0.012:
                env *= remain / 0.012
            mix[index] += int(low * env * amp)

    def add_pad(note: dict) -> None:
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        amp = (note["velocity"] / 127.0) * 2800.0
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            triangle = 1.0 - 4.0 * abs(phase - 0.5)
            t = (index - start) / SR
            remain = (end - index) / SR
            env = 0.85
            if t < 0.08:
                env *= t / 0.08
            if remain < 0.12:
                env *= remain / 0.12
            mix[index] += int(triangle * env * amp)

    roles = {
        "bass": add_bass,
        "harmonic-reference": add_pad,
    }
    rendered = []
    for part in parts:
        voice = roles[part["role"]]
        for note in part["notes"]:
            voice(note)
        rendered.append({"id": part["id"], "role": part["role"], "notes": len(part["notes"])})

    peak = 0
    for sample in mix:
        magnitude = sample if sample >= 0 else -sample
        if magnitude > peak:
            peak = magnitude
    if peak == 0:
        raise RuntimeError("preview mix is silent")
    scale = 1.0 if peak <= 28000 else 28000.0 / peak
    pcm = array("h")
    for sample in mix:
        value = int(sample * scale)
        if value > 32767:
            value = 32767
        elif value < -32768:
            value = -32768
        pcm.append(value)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())
    sample_peak = int(peak * scale)
    return {
        "renderer": RENDERER_VERSION,
        "sample_rate": SR,
        "channels": 1,
        "sample_format": "signed 16-bit little-endian PCM",
        "samples": total,
        "seconds": container_seconds(container_ticks, tempo_us),
        "rounding": "sample = floor(seconds * sample_rate + 0.5), computed from tick 0; intervals are not summed",
        "sample_peak": sample_peak,
        "sample_peak_dbfs": 20.0 * math.log10(sample_peak / 32768.0),
        "sample_peak_note": "This is a sample peak of the integer mix after scaling. It is not a true-peak measurement and it is not LUFS.",
        "voices": rendered,
        "mapping": {
            "bass": "filtered saw pulse, faster decay on short notes, held for the written duration",
            "harmonic-reference": "quiet triangle pad held for the written duration",
        },
        "mapping_note": "These voices are preview mappings. They are not encoded in the MIDI file.",
    }
