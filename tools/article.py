"""Factual article draft. Not published."""

from __future__ import annotations

from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

TITLE = "Synthwave Basslines is a note-only MIDI study pack"
SUBTITLE = "Eight pulsing bass studies, a matched byte check, and a simple-synth preview that is not a master"
TAGS = ["midi", "synthwave", "bass", "music-production", "composition"]
TAG_LINE = "Tags: " + ", ".join(TAGS)

PARAGRAPHS = [
    "DRAFT. " + PUBLICATION,
    TAG_LINE,
    "The pack is eight synthwave bass studies in 4/4. Tempos are integers from 85 to 120 BPM. Container lengths were chosen before the notes. Gate Pulse is 8 bars at 100 BPM. The encoded MP3 of that study measures __PREVIEW_SECONDS__ seconds. Offbeat Neon is 16 bars at 110, Long Fifth is 8 bars at 90, Dotted Drive is 16 bars at 118, Rest Leap is 8 bars at 85, Sixteenth Burst is 16 bars at 120, Syncopated Arc is 8 bars at 96, and Pedal Climb is 16 bars at 108. Sixteen bars at 85 BPM would be about 45 seconds, so that length was not used.",
    "Bass is the core part. Each study has two bass variations, so the core count is sixteen files. Each study also has two harmonic-reference files. Those sixteen files are not part of the core count, and they are not merged into the bass files. Pair bass A with harmonic A, and bass B with harmonic B. The variations are alternatives.",
    "A variation has to change the line. Holding the same notes and only editing velocity does not count. Gate Pulse is six short gates and a rest on beat 4, with octave leaps in the later bars. Offbeat Neon attacks on the ands, so the downbeats stay empty. Long Fifth holds a note for most of the bar, then leaves a rest. Dotted Drive is a dotted eighth plus a sixteenth, three times, then a rest. Rest Leap is a short note, a long rest, and a short octave leap. Sixteenth Burst is two groups of four sixteenths with rests between them, not one continuous sixteenth pattern copied eight times. Syncopated Arc picks up into beat 2 and answers on beat 4. Pedal Climb holds a low pedal, walks up the scale, then leaps an octave into a held last bar.",
    "Bass notes stay between MIDI 28 and 60 and never overlap. C4 is 60. The resolution is 960 ticks per quarter note. Offsets are 0. The harmonic reference sits between MIDI 60 and 84, up to three notes at once, in its own files. Collections are natural minor. No pitch in this pack is outside its study's collection, so no departure flag is set. A departure flag is only for a pitch that leaves the collection.",
    PROGRAM,
    "Chorus, filters, and sidechain pumps are not in the files. The preview synth uses a filtered saw pulse for the bass and a quiet triangle pad for the harmonic reference. That mapping is documented. It is not a program change.",
    "The primary preview is study 01, Gate Pulse, variation A, for all 8 bars at 100 BPM: the bass file and harmonic reference A together. The encoded file measures __PREVIEW_SECONDS__ seconds. The other studies are in the MIDI and are not in that audio file. "
    + PREVIEW_LINE
    + ". The film takes its audio from that preview file and shows the words "
    + ON_PICTURE
    + " on the picture and in the WebVTT captions.",
    AUDITION
    + " The validator reopened the MIDI bytes and compared them with the canonical score. That is a structural check. The sample peak written beside the preview is the peak of the integer mix.",
    "The stills are procedural illustrations of a neon night road with pulsing gates. Amber marks the tall octave peaks. They are not photographs of a session or of performers.",
    "When a public URL exists, use either the combined arrangement or the separate parts. " + WARNING,
    "Call to action: the MIDI, the matched report, and the preview belong together. Do not publish this draft to Medium, Instagram, or X from the draft files alone.",
]


def apply_measured_preview(seconds: str) -> None:
    """Replace the placeholder with the ffprobe duration of the encoded MP3."""
    for index, paragraph in enumerate(PARAGRAPHS):
        PARAGRAPHS[index] = paragraph.replace("__PREVIEW_SECONDS__", seconds)


def markdown() -> str:
    body = "\n\n".join(PARAGRAPHS)
    return f"# {TITLE}\n\n{SUBTITLE}\n\n{body}\n"


def plain_text() -> str:
    lines = [TITLE, "", SUBTITLE, "", *PARAGRAPHS, ""]
    return "\n".join(lines) + "\n"
