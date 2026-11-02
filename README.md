# Synthwave Basslines

Original note-only MIDI studies of pulsing synthwave bass lines. Eight studies, two variations of the bass. Each line has its own rhythm: gates, offbeats, long notes, dotted pairs, sparse leaps, sixteenth bursts, anticipations, or a pedal and climb. Harmonic references are cataloged separately and are not part of the core count. They are not merged into the bass files.

Lengths were chosen before the notes. Nominal seconds = bars * 4 * 60 / BPM. Every study is between 10 and 40 seconds. Sixteen bars at 85 BPM would be about 45 seconds, so that container was not used.

This repository is the pack. The GitHub repository is https://github.com/mizcausevic-dev/synthwave-basslines and it is public. The catalog page is https://mizcausevic-dev.github.io/synthwave-basslines/ .

## What you can open

- `index.html` is the file catalog. The bass staff is drawn from the MIDI bytes. Octave leaps and rests are marked. The harmonic reference opens in its own lane.
- `media.html` is the stills page. The film sits under the pictures.
- `midi/arrangement.mid` is a Format 1 preview arrangement of study 01, variation A: bass and harmonic reference.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is 19.200 seconds in the encoded file. preview, not a master.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `preview, not master`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.

## Studies

- s01 Gate Pulse: 100 BPM, 8 bars, 19.20 seconds, A natural minor, tonic reference A.
- s02 Offbeat Neon: 110 BPM, 16 bars, 34.91 seconds, D natural minor, tonic reference D.
- s03 Long Fifth: 90 BPM, 8 bars, 21.33 seconds, F natural minor, tonic reference F.
- s04 Dotted Drive: 118 BPM, 16 bars, 32.54 seconds, E natural minor, tonic reference E.
- s05 Rest Leap: 85 BPM, 8 bars, 22.59 seconds, C natural minor, tonic reference C.
- s06 Sixteenth Burst: 120 BPM, 16 bars, 32.00 seconds, G natural minor, tonic reference G.
- s07 Syncopated Arc: 96 BPM, 8 bars, 20.00 seconds, Bb natural minor, tonic reference Bb.
- s08 Pedal Climb: 108 BPM, 16 bars, 35.56 seconds, B natural minor, tonic reference B.

Core files: 16. Reference files: 16.

Bass is monophonic and uses MIDI notes 28 to 60 only. C4 is 60. The harmonic reference is not core. It uses MIDI 60 to 84, at most three notes at once, in its own files. PPQ is 960. Meter is 4/4. Offsets are 0. Seeds identify studies and are not random draws. Generator 1.0.0. Rhythm, register, and accent are written on each study.

## Preview path

The preview renders the canonical notes for `s01.bass.a` and `s01.harmonic.a` with `simple-synth-1.0.0`. Tempo authority is the encoded microsecond value in the MIDI, 600000 us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from tick 0. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a filtered saw pulse for the bass and a quiet triangle for the harmonic reference. No program changes are encoded. A conventional GM player will normally use its default piano program for pitched channels unless configured otherwise; compatible GM channel 10 percussion is treated separately. Player behavior may vary. The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: 19.200 seconds. MP3 container probe 19.200 seconds. MP4 probe 19.200 seconds. The film ends on a video frame, so it is slightly shorter than the MP3 container. The music is the same preview, not a different excerpt. The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

No human listening audition was performed for this build. A sample peak is recorded in the preview manifest. It is not LUFS and it is not a true peak.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 43151
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, bass range 28 to 60, monophonic bass, harmonic range 60 to 84 with a polyphony cap of three, note-off before note-on at a shared tick, absence of program changes and other channel messages, departure flags against the declared pitch-class set, agreement with the canonical score, and agreement between `arrangement.mid` and the two source files. A negative overlap fixture is written outside the delivered MIDI and must be rejected.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. This repository is public, so the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Prepared repository description: Original note-only MIDI studies of synthwave bass lines, with matched validation and a simple-synth preview.

Prepared topics: midi, synthwave, bass, music-production, composition.

No release tag was created. `index.html` keeps its name because players and links depend on it. This page is the file catalog the pack requires. GitHub Pages serves the gh-pages branch.

## Limitations

Variation compatibility is per study and is written on the page. Variation A and variation B of a study are alternatives. Pair harmonic A with bass A, and harmonic B with bass B. The arrangement is only study 01. Stacking it with the part files doubles those notes. These lines are original. They are not reconstructions of known bass themes.
