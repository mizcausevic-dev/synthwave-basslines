"""Original synthwave bass studies.

Container lengths and tempos were fixed before any note was written.
Nominal seconds = bars * 4 * 60 / BPM. Every study lands between 10 and 40
seconds. Sixteen bars at 85 BPM would be about 45 seconds and was rejected.

Bass is the core part: monophonic, MIDI 28 to 60. The harmonic reference is
not core. Offsets are 0. Nothing here is a reconstruction of a known theme.

Lengths:
  s01 Gate Pulse       8 bars  100 BPM  19.20 s
  s02 Offbeat Neon    16 bars  110 BPM  34.91 s
  s03 Long Fifth       8 bars   90 BPM  21.33 s
  s04 Dotted Drive    16 bars  118 BPM  32.54 s
  s05 Rest Leap        8 bars   85 BPM  22.59 s
  s06 Sixteenth Burst 16 bars  120 BPM  32.00 s
  s07 Syncopated Arc   8 bars   96 BPM  20.00 s
  s08 Pedal Climb     16 bars  108 BPM  35.56 s
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "synthwave-basslines"
PACK_NAME = "Synthwave Basslines"
BAR = BAR_TICKS_4_4


class Part:
    def __init__(self, study, part_id, role, variation, core, channel, slug, mono, poly, lo, hi):
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = slug
        self.monophonic = mono
        self.max_poly = poly
        self.lo = lo
        self.hi = hi
        self.container_ticks = study["bars"] * BAR
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not self.lo <= pitch <= self.hi:
            raise ValueError(f"{self.part_id} pitch {pitch}")
        if not 1 <= velocity <= 127:
            raise ValueError(f"{self.part_id} velocity {velocity}")
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                if other["pitch"] == pitch or self.monophonic:
                    raise ValueError(f"{self.part_id} overlap {pitch}@{start}")
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} poly {active}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda note: (note["performed_start"], note["pitch"]))
        if self.core and len(ordered) < 8:
            raise ValueError(f"{self.part_id} too few notes")
        if not ordered:
            raise ValueError(f"{self.part_id} empty")
        for index, note in enumerate(ordered, 1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        return {
            "id": self.part_id,
            "study_id": self.study["id"],
            "slug": self.study["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": self.core,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.study["bars"],
            "bpm": self.study["bpm"],
            "tempo_us": self.study["tempo_us"],
            "notes": ordered,
        }


def bass(study, variation):
    return Part(
        study, f"{study['id']}.bass.{variation}", "bass", variation, True, 0,
        f"bass-{variation}", True, 1, 28, 60,
    )


def harmonic(study, variation):
    return Part(
        study, f"{study['id']}.harmonic.{variation}", "harmonic-reference", variation, False, 1,
        f"harmonic-{variation}", False, 3, 60, 84,
    )


def lay(part, bars):
    if len(bars) != part.study["bars"]:
        raise ValueError(f"{part.part_id} bar count {len(bars)}")
    for index, events in enumerate(bars):
        for offset, duration, pitch, velocity in events:
            part.add(index * BAR + offset, duration, pitch, velocity, departure=False)


def gates(pitches, velocity):
    offsets = (0, 480, 960, 1440, 1920, 2400)
    return [
        (offset, 300, pitch, 112 if slot >= 4 else velocity)
        for slot, (offset, pitch) in enumerate(zip(offsets, pitches))
    ]


def offbeats(pitches, velocity):
    offsets = (480, 1440, 2400, 3360)
    return [
        (offset, 360, pitch, velocity if slot % 2 == 0 else min(120, velocity + 16))
        for slot, (offset, pitch) in enumerate(zip(offsets, pitches))
    ]


def dotted(pitches, velocity):
    pattern = ((0, 700), (720, 220), (960, 700), (1680, 220), (1920, 700), (2640, 220))
    return [
        (offset, duration, pitch, velocity if duration == 700 else min(122, velocity + 18))
        for (offset, duration), pitch in zip(pattern, pitches)
    ]


def bursts(low, high, velocity, second=True):
    notes = [(offset, 180, low, velocity) for offset in (0, 240, 480, 720)]
    if second:
        notes += [
            (offset, 180, high, min(122, velocity + 14))
            for offset in (1920, 2160, 2400, 2640)
        ]
    return notes


def repeat(pattern, count):
    return [list(pattern) for _ in range(count)]


def harmony(study, variation, plan):
    part = harmonic(study, variation)
    offset = 0 if variation == "a" else 960
    trim = 0 if variation == "a" else 1920
    for start_bar, length, pitches in plan:
        chosen = pitches if variation == "a" else pitches[:2]
        start = start_bar * BAR + offset
        duration = length * BAR - trim
        velocity = 64 if variation == "a" else 72
        for index, pitch in enumerate(chosen):
            part.add(start, duration, pitch, velocity + index * 4, departure=False)
    return part


def _s01(study):
    a = bass(study, "a")
    b = bass(study, "b")
    lay(a, [
        gates((45, 45, 45, 45, 45, 45), 84),
        gates((45, 45, 45, 45, 45, 45), 90),
        gates((45, 45, 45, 45, 57, 57), 96),
        gates((57, 57, 45, 45, 45, 45), 100),
        gates((40, 40, 40, 40, 40, 40), 86),
        gates((40, 40, 52, 52, 40, 40), 104),
        gates((36, 36, 36, 36, 36, 36), 90),
        [(0, 300, 36, 96), (480, 300, 48, 118), (960, 900, 36, 108)],
    ])
    lay(b, [
        [(240, 480, 36, 88), (1200, 240, 36, 96), (1680, 720, 48, 112), (2880, 600, 36, 90)],
        [(240, 480, 36, 90), (1200, 240, 48, 108), (1680, 720, 36, 100), (2880, 600, 36, 88)],
        [(240, 480, 33, 86), (1200, 240, 33, 94), (1680, 720, 45, 114), (2880, 600, 33, 90)],
        [(240, 480, 33, 92), (1200, 240, 45, 110), (1680, 720, 33, 100), (2880, 600, 40, 96)],
        [(240, 480, 40, 88), (1200, 240, 40, 96), (1680, 720, 52, 116), (2880, 600, 40, 90)],
        [(240, 480, 40, 94), (1200, 240, 52, 112), (1680, 720, 40, 104), (2880, 600, 43, 98)],
        [(240, 480, 43, 90), (1200, 240, 43, 100), (1680, 720, 31, 112), (2880, 600, 43, 92)],
        [(240, 480, 48, 100), (1200, 240, 36, 108), (1680, 720, 48, 118), (2880, 600, 45, 96)],
    ])
    plan = [(0, 4, (69, 72, 76)), (4, 4, (64, 67, 71))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s02(study):
    a = bass(study, "a")
    b = bass(study, "b")
    bars_a = []
    for index in range(15):
        if index < 4:
            pitches = (38, 38, 38, 38)
        elif index < 8:
            pitches = (38, 50, 38, 50)
        elif index < 12:
            pitches = (45, 41, 38, 50)
        else:
            pitches = (38, 41, 45, 36)
        bars_a.append(offbeats(pitches, 84 + (index % 4) * 6))
    bars_a.append([(480, 1440, 38, 102), (2400, 1200, 50, 118)])
    lay(a, bars_a)
    triples = (
        [(45, 45, 38)] * 4
        + [(50, 38, 45)] * 4
        + [(33, 45, 38)] * 4
        + [(38, 50, 41)] * 4
    )
    lay(b, [
        [(0, 840, one, 88), (960, 840, two, 98), (2880, 720, three, 112)]
        for one, two, three in triples
    ])
    plan = [(0, 8, (62, 65, 69)), (8, 8, (70, 74, 77))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s03(study):
    a = bass(study, "a")
    b = bass(study, "b")
    lay(a, [
        [(0, 2760, 29, 88)],
        [(960, 1920, 36, 96)],
        [(0, 2760, 29, 92)],
        [(960, 1920, 48, 114)],
        [(0, 2760, 41, 100)],
        [(960, 1920, 48, 108)],
        [(0, 2760, 44, 96)],
        [(0, 3600, 41, 116)],
    ])
    rows = (
        (44, 48, 41, 36),
        (41, 44, 48, 41),
        (29, 41, 48, 44),
        (36, 48, 41, 53),
        (53, 48, 44, 41),
        (44, 41, 36, 48),
        (41, 53, 48, 44),
        (29, 41, 53, 48),
    )
    lay(b, [
        [(0, 480, row[0], 86), (480, 480, row[1], 92), (960, 480, row[2], 100), (1920, 1440, row[3], 112)]
        for row in rows
    ])
    plan = [(0, 4, (65, 68, 72)), (4, 4, (60, 63, 67))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s04(study):
    a = bass(study, "a")
    b = bass(study, "b")
    bars_a = []
    for index in range(15):
        if index < 4:
            pitches = (40, 40, 40, 40, 40, 40)
        elif index < 8:
            pitches = (40, 52, 40, 52, 40, 52)
        elif index < 12:
            pitches = (47, 35, 47, 35, 47, 35)
        else:
            pitches = (43, 43, 43, 43, 43, 43)
        bars_a.append(dotted(pitches, 86 + (index % 4) * 6))
    bars_a.append([(0, 1920, 40, 104), (2400, 1200, 52, 120)])
    lay(a, bars_a)
    triples = (
        [(43, 47, 40)] * 4
        + [(40, 52, 47)] * 4
        + [(47, 35, 40)] * 4
        + [(43, 59, 52)] * 4
    )
    lay(b, [
        [(360, 600, one, 90), (1440, 1200, two, 108), (3120, 480, three, 98)]
        for one, two, three in triples
    ])
    plan = [(0, 8, (64, 67, 71)), (8, 8, (62, 66, 69))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s05(study):
    a = bass(study, "a")
    b = bass(study, "b")
    lay(a, [
        [(0, 840, 36, 92), (1920, 360, 48, 116)],
        [(0, 840, 36, 94), (1920, 360, 48, 114)],
        [(0, 840, 43, 96), (1920, 360, 55, 118)],
        [(0, 840, 43, 98), (1920, 360, 31, 112)],
        [(0, 840, 44, 100), (1920, 360, 56, 118)],
        [(0, 840, 41, 96), (1920, 360, 29, 110)],
        [(0, 1920, 36, 104)],
        [(480, 3000, 48, 116)],
    ])
    pairs = (
        (51, 39), (51, 39), (46, 43), (48, 36),
        (39, 51), (43, 31), (36, 48), (29, 41),
    )
    lay(b, [
        [(1440, 480, low, 94), (2400, 960, high, 112)]
        for low, high in pairs
    ])
    plan = [(0, 4, (60, 63, 67)), (4, 4, (68, 72, 75))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s06(study):
    a = bass(study, "a")
    b = bass(study, "b")
    bars_a = []
    for index in range(12):
        if index < 4:
            bars_a.append(bursts(43, 43, 86))
        elif index < 8:
            bars_a.append(bursts(43, 55, 92))
        else:
            bars_a.append(bursts(46, 50, 98))
    for pitch, velocity in ((43, 100), (41, 104), (39, 108), (38, 112)):
        bars_a.append(bursts(pitch, pitch, velocity, second=False))
    lay(a, bars_a)
    cycle = [
        43, 46, 48, 50, 53, 55, 55, 50, 46, 43, 55, 43,
        46, 50, 43, 48, 36, 48, 41, 53, 41, 39, 51, 39,
        55, 50, 46, 43, 48, 36, 53, 41, 50, 43, 38, 50,
        36, 43, 55, 46, 39, 51, 48, 36, 43, 53, 41, 55,
    ]
    if len(cycle) != 48:
        raise ValueError(len(cycle))
    grouped = [cycle[index:index + 3] for index in range(0, 48, 3)]
    lay(b, [
        [(0, 720, one, 88), (1440, 720, two, 102), (2880, 480, three, 96)]
        for one, two, three in grouped
    ])
    plan = [(0, 8, (67, 70, 74)), (8, 8, (63, 67, 70))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s07(study):
    a = bass(study, "a")
    b = bass(study, "b")

    def arc(pitches, velocity):
        offsets = ((720, 200), (960, 1320), (2880, 600))
        return [
            (offset, duration, pitch, velocity if slot < 2 else min(122, velocity + 16))
            for slot, ((offset, duration), pitch) in enumerate(zip(offsets, pitches))
        ]

    lay(a, [
        arc((46, 46, 58), 88),
        arc((46, 46, 58), 94),
        arc((41, 41, 53), 90),
        arc((41, 41, 53), 98),
        arc((37, 49, 37), 92),
        arc((37, 49, 37), 100),
        [(0, 1680, 34, 102), (2400, 960, 46, 116)],
        [(0, 3600, 46, 110)],
    ])
    rows = (
        (41, 41, 41, 58),
        (41, 53, 41, 58),
        (53, 53, 46, 58),
        (46, 46, 34, 46),
        (34, 46, 53, 58),
        (41, 58, 46, 34),
        (53, 41, 58, 46),
        (34, 46, 58, 41),
    )
    lay(b, [
        [(0, 400, row[0], 86), (480, 400, row[1], 94), (960, 400, row[2], 102), (1440, 400, row[3], 114)]
        for row in rows
    ])
    plan = [(0, 4, (70, 73, 77)), (4, 4, (66, 70, 73))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


def _s08(study):
    a = bass(study, "a")
    b = bass(study, "b")
    climb = [
        35, 37, 38, 40, 42, 43, 45, 47, 49, 50, 52, 54,
        55, 57, 59, 57, 55, 54, 52, 50, 49, 47, 45, 43,
    ]
    if len(climb) != 24:
        raise ValueError(len(climb))
    bars_a = [((0, 1680, 35, 90), (2400, 960, 35, 104)) for _ in range(4)]
    groups = [climb[index:index + 3] for index in range(0, 24, 3)]
    for group in groups:
        bars_a.append([
            (0, 480, group[0], 92),
            (960, 480, group[1], 100),
            (1920, 960, group[2], 110),
        ])
    bars_a.append([(0, 360, 35, 96), (480, 1440, 47, 116), (2400, 480, 35, 100)])
    bars_a.append([(0, 360, 47, 100), (480, 1440, 59, 120), (2400, 480, 47, 104)])
    bars_a.append([(0, 360, 35, 98), (480, 1440, 59, 118), (2400, 480, 47, 106)])
    bars_a.append([(0, 3360, 47, 112)])
    lay(a, bars_a)
    descent = [
        54, 52, 50, 49, 47, 45, 43, 42, 40, 38, 37, 35,
        59, 54, 47, 42, 59, 47, 54, 40, 52, 35, 47, 37,
        50, 43, 35, 47, 59, 42, 38, 50, 35, 45, 57, 40,
        52, 47, 35, 59, 54, 43, 49, 37, 45, 59, 42, 35,
        47, 59, 35, 54, 40, 52, 45, 37, 50, 59, 42, 35,
        38, 47, 59, 35, 52, 40, 45, 54, 37, 49, 59, 42,
        35, 47, 59, 43, 54, 38, 50, 35, 57, 45, 40, 52,
        59, 47, 35, 42, 54, 37, 45, 59, 40, 50, 35, 47,
    ]
    if len(descent) != 96:
        raise ValueError(len(descent))
    grouped = [descent[index:index + 6] for index in range(0, 96, 6)]
    pattern = ((0, 240), (240, 240), (720, 1200), (2400, 240), (2640, 240), (3120, 480))
    velocities = (82, 90, 108, 88, 96, 100)
    lay(b, [
        [
            (offset, duration, pitch, velocity)
            for (offset, duration), pitch, velocity in zip(pattern, group, velocities)
        ]
        for group in grouped
    ])
    plan = [(0, 8, (71, 74, 78)), (8, 8, (67, 71, 74))]
    return [a, b, harmony(study, "a", plan), harmony(study, "b", plan)]


BUILDERS = {
    "s01": _s01,
    "s02": _s02,
    "s03": _s03,
    "s04": _s04,
    "s05": _s05,
    "s06": _s06,
    "s07": _s07,
    "s08": _s08,
}


def studies():
    common = {
        "meter": "4/4",
        "bar_ticks": BAR,
        "ppq": PPQ,
        "stochastic_draws": 0,
    }
    rows = [
        {**common, "id": "s01", "slug": "s01-gate-pulse", "title": "Gate Pulse", "bpm": 100, "bars": 8,
         "tonic": "A", "tonal_reference": "A", "collection_name": "A natural minor",
         "pitch_classes": [0, 2, 4, 5, 7, 9, 11], "departures": [], "seed": 10001,
         "harmonic_rhythm": "Four bars of Am, then four bars of Em.",
         "rhythm": "Six gated eighths and a rest on beat 4. The last bar keeps three notes and a longer rest.",
         "changes": ["Am", "Am leap", "Em", "C turn"], "change_bars": [2, 2, 2, 2],
         "phrases": [
             {"name": "Pulse", "start_bar": 0, "bars": 2},
             {"name": "Leap", "start_bar": 2, "bars": 2},
             {"name": "Fifth", "start_bar": 4, "bars": 2},
             {"name": "Turn", "start_bar": 6, "bars": 2},
         ],
         "identity": "Six short gates on the eighth grid and a rest on beat 4. Bars 3, 6, and 8 leap an octave. Variation B starts a 16th later, holds longer notes, and begins on C instead of A.",
         "limitations": "Use bass A with harmonic A, and bass B with harmonic B. The beat-4 silence is the gate. Do not fill it.",
         "accent": "The last two gates of a bar are louder. The octave leap is the peak."},
        {**common, "id": "s02", "slug": "s02-offbeat-neon", "title": "Offbeat Neon", "bpm": 110, "bars": 16,
         "tonic": "D", "tonal_reference": "D", "collection_name": "D natural minor",
         "pitch_classes": [0, 2, 4, 5, 7, 9, 10], "departures": [], "seed": 11002,
         "harmonic_rhythm": "Eight bars of Dm, then eight bars of Bb.",
         "rhythm": "Four offbeat attacks. Downbeats are rests until the last bar lengthens two of them.",
         "changes": ["Dm", "D octave", "A F", "Arrive"], "change_bars": [4, 4, 4, 4],
         "phrases": [
             {"name": "Offbeat", "start_bar": 0, "bars": 4},
             {"name": "Octave", "start_bar": 4, "bars": 4},
             {"name": "Answer", "start_bar": 8, "bars": 4},
             {"name": "Arrive", "start_bar": 12, "bars": 4},
         ],
         "identity": "Attacks sit on the and of each beat, so every downbeat is a rest. D2 answers D3 in the second phrase. Variation B plays beats 1, 2, and 4 and starts on A.",
         "limitations": "The offbeat grid is the hook. Variation B is not a shifted copy of the same durations.",
         "accent": "The even offbeats are louder than the odd ones. The last bar is the peak."},
        {**common, "id": "s03", "slug": "s03-long-fifth", "title": "Long Fifth", "bpm": 90, "bars": 8,
         "tonic": "F", "tonal_reference": "F", "collection_name": "F natural minor",
         "pitch_classes": [0, 1, 3, 5, 7, 8, 10], "departures": [], "seed": 9003,
         "harmonic_rhythm": "Four bars of Fm, then four bars of C.",
         "rhythm": "Even bars hold one note and rest at the end. Odd bars enter a quarter late, except the final hold.",
         "changes": ["F low", "Fifth", "F lift", "Cadence"], "change_bars": [2, 2, 2, 2],
         "phrases": [
             {"name": "Low", "start_bar": 0, "bars": 2},
             {"name": "Fifth", "start_bar": 2, "bars": 2},
             {"name": "Lift", "start_bar": 4, "bars": 2},
             {"name": "Cadence", "start_bar": 6, "bars": 2},
         ],
         "identity": "Long notes with a rest at the end of even bars. The leap from F1 to C3 is wider than an octave. Variation B replaces each hold with four attacks.",
         "limitations": "The long notes are written durations, not a pedal controller. Nothing in the file sustains past its note-off.",
         "accent": "The late fifth is louder than the low F. The final hold is the peak."},
        {**common, "id": "s04", "slug": "s04-dotted-drive", "title": "Dotted Drive", "bpm": 118, "bars": 16,
         "tonic": "E", "tonal_reference": "E", "collection_name": "E natural minor",
         "pitch_classes": [0, 2, 4, 6, 7, 9, 11], "departures": [], "seed": 11804,
         "harmonic_rhythm": "Eight bars of Em, then eight bars of D.",
         "rhythm": "Dotted eighth plus sixteenth, three times, then a rest on beat 4. The last bar is two longer notes.",
         "changes": ["Em motor", "Octave 16ths", "Low B", "Landing"], "change_bars": [4, 4, 4, 4],
         "phrases": [
             {"name": "Motor", "start_bar": 0, "bars": 4},
             {"name": "Leap", "start_bar": 4, "bars": 4},
             {"name": "Low B", "start_bar": 8, "bars": 4},
             {"name": "Landing", "start_bar": 12, "bars": 4},
         ],
         "identity": "A dotted eighth and a sixteenth, three pairs, then silence on beat 4. The sixteenths leap to E3, then down to B1. Variation B leaves that grid for three notes starting after a 16th.",
         "limitations": "The dot is the written duration. No swing offset is stored.",
         "accent": "Each sixteenth is louder than the dotted note before it."},
        {**common, "id": "s05", "slug": "s05-rest-leap", "title": "Rest Leap", "bpm": 85, "bars": 8,
         "tonic": "C", "tonal_reference": "C", "collection_name": "C natural minor",
         "pitch_classes": [0, 2, 3, 5, 7, 8, 10], "departures": [], "seed": 8505,
         "harmonic_rhythm": "Four bars of Cm, then four bars of Ab.",
         "rhythm": "A note on beat 1, a long rest, a short leap, and another rest. The last two bars change the spacing.",
         "changes": ["C leap", "G leap", "Ab F", "Arrive"], "change_bars": [2, 2, 2, 2],
         "phrases": [
             {"name": "Rest", "start_bar": 0, "bars": 2},
             {"name": "Leap", "start_bar": 2, "bars": 2},
             {"name": "Drop", "start_bar": 4, "bars": 2},
             {"name": "Arrive", "start_bar": 6, "bars": 2},
         ],
         "identity": "Beat 1, a long rest, a short octave leap, and another rest. Variation B is silent on beat 1 and answers in the middle of the bar, often moving down.",
         "limitations": "The empty beats are the line. Do not quantize them into a busier pulse.",
         "accent": "The short leap is louder than the downbeat."},
        {**common, "id": "s06", "slug": "s06-sixteenth-burst", "title": "Sixteenth Burst", "bpm": 120, "bars": 16,
         "tonic": "G", "tonal_reference": "G", "collection_name": "G natural minor",
         "pitch_classes": [0, 2, 3, 5, 7, 9, 10], "departures": [], "seed": 12006,
         "harmonic_rhythm": "Eight bars of Gm, then eight bars of Eb.",
         "rhythm": "Two bursts of four sixteenths with rests between and after them. The last four bars keep only the first burst.",
         "changes": ["Gm burst", "Octave burst", "Bb D", "Thin"], "change_bars": [4, 4, 4, 4],
         "phrases": [
             {"name": "Burst", "start_bar": 0, "bars": 4},
             {"name": "High burst", "start_bar": 4, "bars": 4},
             {"name": "Color", "start_bar": 8, "bars": 4},
             {"name": "Thin", "start_bar": 12, "bars": 4},
         ],
         "identity": "Four sixteenths, a rest, four sixteenths, a rest. The second burst leaps to G3. This is not one eighth-note cell transposed through eight studies. Variation B walks in three longer notes.",
         "limitations": "The gaps inside a burst are shorter than an eighth and are not the structural rests. The structural rests are the holes between bursts.",
         "accent": "The second burst is louder than the first."},
        {**common, "id": "s07", "slug": "s07-syncopated-arc", "title": "Syncopated Arc", "bpm": 96, "bars": 8,
         "tonic": "Bb", "tonal_reference": "Bb", "collection_name": "Bb natural minor",
         "pitch_classes": [0, 1, 3, 5, 6, 8, 10], "departures": [], "seed": 9607,
         "harmonic_rhythm": "Four bars of Bbm, then four bars of Gb.",
         "rhythm": "A 16th pickup into beat 2, a held note, a rest, and a short answer on beat 4. The ending changes the grid.",
         "changes": ["Bb push", "F push", "Db", "Hold"], "change_bars": [2, 2, 2, 2],
         "phrases": [
             {"name": "Push", "start_bar": 0, "bars": 2},
             {"name": "Fifth", "start_bar": 2, "bars": 2},
             {"name": "Descent", "start_bar": 4, "bars": 2},
             {"name": "Hold", "start_bar": 6, "bars": 2},
         ],
         "identity": "The line anticipates beat 2, holds, rests, and answers an octave up on beat 4. Variation B drops the pickup and plays four even attacks from the downbeat.",
         "limitations": "The anticipation is an earlier start, not a negative offset. Nothing begins before tick 0.",
         "accent": "The beat-4 answer is the loud note of the bar."},
        {**common, "id": "s08", "slug": "s08-pedal-climb", "title": "Pedal Climb", "bpm": 108, "bars": 16,
         "tonic": "B", "tonal_reference": "B", "collection_name": "B natural minor",
         "pitch_classes": [1, 2, 4, 6, 7, 9, 11], "departures": [], "seed": 10808,
         "harmonic_rhythm": "Eight bars of Bm, then eight bars of G.",
         "rhythm": "A low pedal with a rest before the last beat, then a three-note climb, then octave leaps into a held final bar.",
         "changes": ["Pedal", "Climb", "Climb down", "Leap"], "change_bars": [4, 4, 4, 4],
         "phrases": [
             {"name": "Pedal", "start_bar": 0, "bars": 4},
             {"name": "Climb", "start_bar": 4, "bars": 4},
             {"name": "Return", "start_bar": 8, "bars": 4},
             {"name": "Leap", "start_bar": 12, "bars": 4},
         ],
         "identity": "Four bars of B1 with a rest before beat 4, eight bars climbing the scale, then octave leaps and a held B2. Variation B is a six-note gallop that starts on F sharp and moves downward.",
         "limitations": "The pedal is repeated notes with a rest, not a tied controller. Pair variation B's gallop only with harmonic B.",
         "accent": "The note before the rest is louder than the pickup of the pedal. The octave peak is the loudest."},
    ]
    for row in rows:
        if not isinstance(row["bpm"], int) or isinstance(row["bpm"], bool) or not 85 <= row["bpm"] <= 120:
            raise ValueError(row["bpm"])
        if sum(row["change_bars"]) != row["bars"] or len(row["change_bars"]) != len(row["changes"]):
            raise ValueError(row["id"] + " changes")
        if sum(item["bars"] for item in row["phrases"]) != row["bars"]:
            raise ValueError(row["id"] + " phrases")
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        row["nominal_seconds"] = row["bars"] * 4 * 60 / row["bpm"]
        if not 10 <= row["nominal_seconds"] <= 40:
            raise ValueError(f"{row['id']} seconds {row['nominal_seconds']}")
    return rows


def _sig(notes):
    return [(note["performed_start"], note["pitch"], note["duration"]) for note in notes]


def _attack_tuple(notes):
    return tuple((note["performed_start"], note["duration"]) for note in notes if note["performed_start"] < BAR)


def assert_collections(catalog_studies, parts):
    allowed = {study["id"]: set(study["pitch_classes"]) for study in catalog_studies}
    for part in parts:
        pool = allowed[part["study_id"]]
        for note in part["notes"]:
            inside = (note["pitch"] % 12) in pool
            if note["departure"] and inside:
                raise ValueError(f"{part['id']} departure {note['pitch']} is inside the collection")
            if not note["departure"] and not inside:
                raise ValueError(f"{part['id']} note {note['pitch']} left the collection")


def assert_identities(parts):
    basses = [part for part in parts if part["role"] == "bass"]
    by = {}
    for part in basses:
        by.setdefault(part["study_id"], {})[part["variation"]] = part
    seen = {}
    report = []
    for study_id in sorted(by):
        left = by[study_id]["a"]["notes"]
        right = by[study_id]["b"]["notes"]
        if _sig(left) == _sig(right):
            raise ValueError(f"{study_id} variations match in start, pitch, and duration")
        if [note["performed_start"] for note in left] == [note["performed_start"] for note in right]:
            raise ValueError(f"{study_id} variations share starts")
        if [note["duration"] for note in left] == [note["duration"] for note in right]:
            raise ValueError(f"{study_id} variations share durations")
        if [note["pitch"] for note in left] == [note["pitch"] for note in right]:
            raise ValueError(f"{study_id} variations share pitches")
        attack = _attack_tuple(left)
        if attack in seen:
            raise ValueError(f"{study_id} attack tuple repeats {seen[attack]}")
        seen[attack] = study_id
        leaps = 0
        rests = 0
        previous = None
        for note in left:
            if previous is not None:
                gap = note["performed_start"] - (previous["performed_start"] + previous["duration"])
                if gap >= 480:
                    rests += 1
                if abs(note["pitch"] - previous["pitch"]) >= 12:
                    leaps += 1
            previous = note
        container = by[study_id]["a"]["container_ticks"]
        if left and left[0]["performed_start"] >= 480:
            rests += 1
        if left and container - (left[-1]["performed_start"] + left[-1]["duration"]) >= 480:
            rests += 1
        if leaps < 1:
            raise ValueError(f"{study_id} has no octave leap")
        if rests < 1:
            raise ValueError(f"{study_id} has no deliberate rest")
        report.append({
            "study_id": study_id,
            "a": len(left),
            "b": len(right),
            "attack_tuple": [list(pair) for pair in attack],
            "octave_leaps": leaps,
            "rests_at_least": rests,
        })
    return {
        "studies": report,
        "method": (
            "Bass variation A and variation B differ in start, pitch, and duration, not velocity alone. "
            "Each variation A first-bar attack tuple is unique. Departure flags are only for pitches outside the collection."
        ),
    }


def compose():
    catalog_studies = studies()
    parts = []
    for study in catalog_studies:
        for part in BUILDERS[study["id"]](study):
            parts.append(part.finish())
    assert_collections(catalog_studies, parts)
    identity = assert_identities(parts)
    core = [part for part in parts if part["core"]]
    refs = [part for part in parts if not part["core"]]
    if len(core) != 16 or len(refs) != 16:
        raise ValueError((len(core), len(refs)))
    preview = next(study for study in catalog_studies if study["id"] == "s01")
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": preview["bars"] * BAR,
        "bpm": preview["bpm"],
        "tempo_us": preview["tempo_us"],
        "meter": "4/4",
        "description": "Study 01 variation A bass with harmonic reference A. The pad is not inside the bass file.",
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Bass", "source_part": "s01.bass.a", "channel": 0},
            {"name": "Harmonic Reference", "source_part": "s01.harmonic.a", "channel": 1},
        ],
    }
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR},
        "c4": 60,
        "bass_range": [28, 60],
        "harmonic_range": [60, 84],
        "note_policy": "note-only MIDI. Filters, chorus, and sidechain are not encoded.",
        "microtiming": "offset is 0; performed_start = nominal_start",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. Nothing is random.",
        "core_part_count": len(core),
        "reference_part_count": len(refs),
        "length_rule": "seconds = bars * 4 * 60 / BPM. Lengths were chosen before notes so every study is between 10 and 40 seconds.",
        "range_statement": "Bass is monophonic and uses MIDI notes 28 to 60 only. C4 is 60. The harmonic reference is not core. It uses MIDI 60 to 84, at most three notes at once, in its own files.",
        "studies": [{
            key: study[key] for key in (
                "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "nominal_seconds",
                "meter", "bar_ticks", "tonic", "tonal_reference", "collection_name", "pitch_classes",
                "departures", "seed", "harmonic_rhythm", "rhythm", "changes", "change_bars", "phrases",
                "identity", "limitations", "accent", "stochastic_draws",
            )
        } for study in catalog_studies],
        "parts": [{
            "id": part["id"],
            "study_id": part["study_id"],
            "role": part["role"],
            "variation": part["variation"],
            "core": part["core"],
            "channel": part["channel"],
            "path": part["path"],
            "notes": len(part["notes"]),
            "container_bars": part["container_bars"],
            "bpm": part["bpm"],
            "monophonic": part["monophonic"],
        } for part in parts],
        "arrangement": arrangement,
        "preview_part_ids": ["s01.bass.a", "s01.harmonic.a"],
        "stack_warning": "Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.",
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangement": arrangement,
        "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
