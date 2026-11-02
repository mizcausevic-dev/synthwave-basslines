"""Catalog page. The bass line is measured from the fetched MIDI files."""

from __future__ import annotations

import json
from pathlib import Path

from tools.article import TAG_LINE, TITLE
from tools.screening import render_media, still_frames
from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

SPELL = {
    "s01": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s02": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "s03": ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "s04": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s05": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "s06": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "s07": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "s08": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
}


def write_page(path: Path, catalog: dict, report: dict, preview: dict, film: dict) -> None:
    path.write_text(render_page(catalog, report, preview, film), encoding="utf-8")
    root = path.parent
    path.with_name("media.html").write_text(render_media({
        "pack_name": catalog["pack_name"],
        "subject": "Cyan pulses are the bass gates. Amber pulses are the octave peaks. Empty slots on the road are rests.",
        "colors": {
            "bg": "#070814",
            "paper": "#e7f6ff",
            "ink": "#071018",
            "accent": "#2ee6d6",
            "muted": "#8ea6bb",
        },
        "frames": still_frames(root),
        "preview_seconds": preview["seconds_encoded"],
        "film_seconds": film["duration_seconds"],
    }), encoding="utf-8")


def _rows(catalog: dict) -> str:
    rows = []
    for part in catalog["parts"]:
        kind = "core" if part["core"] else "harmonic reference"
        rows.append(
            "<tr>"
            f"<td><a href=\"{part['path']}\">{part['id']}</a></td>"
            f"<td>{part['role']}</td>"
            f"<td>{part['variation']}</td>"
            f"<td>{kind}</td>"
            f"<td>{part['bpm']}</td>"
            f"<td>{part['container_bars']}</td>"
            f"<td>{part['notes']}</td>"
            "</tr>"
        )
    return "".join(rows)


def _studies(catalog: dict) -> str:
    blocks = []
    for study in catalog["studies"]:
        seconds = study["nominal_seconds"]
        blocks.append(
            "<li>"
            f"<strong>{study['id']} {study['title']}</strong> "
            f"{study['bpm']} BPM, {study['bars']} bars, {seconds:.2f} seconds, "
            f"{study['collection_name']}, tonic {study['tonal_reference']}. "
            f"{study['rhythm']} {study['limitations']}"
            "</li>"
        )
    return "".join(blocks)


def _map(catalog: dict) -> str:
    grouped: dict[str, list] = {}
    for part in catalog["parts"]:
        grouped.setdefault(part["study_id"], []).append(part)
    cards = []
    for study in catalog["studies"]:
        parts = grouped[study["id"]]
        core = "".join(
            f"<li><a href=\"{part['path']}\">{part['id']}</a></li>"
            for part in parts if part["core"]
        )
        refs = "".join(
            f"<li><a href=\"{part['path']}\">{part['id']}</a></li>"
            for part in parts if not part["core"]
        )
        cards.append(
            "<article class=\"card\">"
            f"<h3>{study['id']} {study['title']}</h3>"
            f"<p>Core bass</p><ul>{core}</ul>"
            f"<p>Harmonic reference, not core</p><ul>{refs}</ul>"
            "</article>"
        )
    return "".join(cards)


def _rules(report: dict) -> str:
    return "".join(f"<li>{rule}</li>" for rule in report["rules"])


def render_page(catalog: dict, report: dict, preview: dict, film: dict) -> str:
    payload = {
        "studies": [
            {
                "id": study["id"],
                "title": study["title"],
                "bpm": study["bpm"],
                "bars": study["bars"],
                "collection": study["collection_name"],
                "tonic": study["tonal_reference"],
                "identity": study["identity"],
                "limitations": study["limitations"],
                "rhythm": study["rhythm"],
                "accent": study["accent"],
                "harmonic_rhythm": study["harmonic_rhythm"],
                "departures": study["departures"],
                "phrases": study["phrases"],
                "tempo_us": study["tempo_us"],
                "changes": study["changes"],
                "change_bars": study["change_bars"],
                "spell": SPELL[study["id"]],
                "nominal_seconds": study["nominal_seconds"],
            }
            for study in catalog["studies"]
        ],
        "parts": [
            {
                "id": part["id"],
                "study_id": part["study_id"],
                "role": part["role"],
                "variation": part["variation"],
                "path": part["path"],
            }
            for part in catalog["parts"]
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    seconds = f"{preview['seconds_encoded']:.3f}"
    film_seconds = f"{film['duration_seconds']:.3f}"
    html = TEMPLATE
    replacements = {
        "__ROWS__": _rows(catalog),
        "__STUDIES__": _studies(catalog),
        "__MAP__": _map(catalog),
        "__RULES__": _rules(report),
        "__RANGE__": catalog["range_statement"],
        "__WARNING__": WARNING,
        "__PROGRAM__": PROGRAM,
        "__AUDITION__": AUDITION,
        "__PUBLICATION__": PUBLICATION,
        "__PREVIEW_LINE__": PREVIEW_LINE,
        "__ON_PICTURE__": ON_PICTURE,
        "__SECONDS__": seconds,
        "__FILM_SECONDS__": film_seconds,
        "__RESULT__": report["result"],
        "__CORE__": str(catalog["core_part_count"]),
        "__REFS__": str(catalog["reference_part_count"]),
        "__TAG_LINE__": TAG_LINE,
        "__ARTICLE_TITLE__": TITLE,
        "__DATA__": data,
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Synthwave Basslines</title>
  <style>
    :root {
      --bg: #070814;
      --ink: #e7f6ff;
      --muted: #8ea6bb;
      --cyan: #2ee6d6;
      --amber: #ffb454;
      --panel: #10182c;
      --line: rgba(46, 230, 214, .28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(900px 280px at 50% 0, rgba(46, 230, 214, .12), transparent 70%),
        var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", "Avenir Next", "Trebuchet MS", sans-serif;
      line-height: 1.45;
    }
    a { color: var(--cyan); }
    h1, h2, h3 { font-weight: 560; letter-spacing: -.02em; }
    h1 { font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: .92; margin: 0 0 12px; }
    h2 { font-size: 1.45rem; margin: 0 0 8px; }
    h3 { font-size: 1rem; margin: 0 0 6px; }
    .wrap { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding-bottom: 48px; }
    .kicker { margin: 0; color: var(--amber); letter-spacing: .16em; text-transform: uppercase; font-size: .74rem; }
    .horizon { height: 2px; margin: 18px 0 26px; background: linear-gradient(90deg, transparent, var(--cyan), var(--amber), transparent); }
    .intro, .bench { display: grid; grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr); gap: 28px; align-items: start; }
    .lede, .meta, .note { color: var(--muted); }
    .hero img, video, audio { display: block; width: 100%; height: auto; background: #000; }
    .hero img { border-radius: 16px; }
    figcaption, .meta, .note, button, .legend { font-family: ui-monospace, Menlo, Consolas, monospace; }
    figcaption { color: var(--muted); font-size: .78rem; margin-top: 6px; }
    button {
      border: 1px solid var(--line); background: transparent; color: var(--ink);
      border-radius: 8px; padding: 8px 12px; cursor: pointer;
    }
    button[aria-pressed="true"] { background: var(--cyan); color: #071018; border-color: var(--cyan); }
    .index { display: flex; flex-direction: column; gap: 8px; }
    .switch, .phrases { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .system { display: grid; grid-template-columns: 44px minmax(0, 1fr); gap: 8px; align-items: start; }
    .axis { margin-top: 26px; height: 392px; position: relative; color: var(--muted); font-size: 10px; }
    .axis span { position: absolute; right: 0; transform: translateY(-50%); }
    .scroller, .pad-scroll { overflow-x: auto; max-width: 100%; background: #070b16; border: 1px solid var(--line); border-radius: 14px; }
    .bars { position: relative; height: 26px; }
    .change { position: absolute; top: 4px; height: 18px; overflow: hidden; white-space: nowrap; color: var(--amber); font-size: 11px; }
    .staff { position: relative; height: 392px; background:
      linear-gradient(to bottom, transparent 11px, rgba(46,230,214,.35) 11px, rgba(46,230,214,.35) 12px, transparent 12px),
      linear-gradient(to bottom, transparent 149px, rgba(46,230,214,.2) 149px, rgba(46,230,214,.2) 150px, transparent 150px),
      linear-gradient(to bottom, transparent 287px, rgba(255,180,84,.25) 287px, rgba(255,180,84,.25) 288px, transparent 288px);
    }
    .pulse, .pad {
      position: absolute; height: 8px; border-radius: 4px; background: var(--cyan); min-width: 2px;
    }
    .pulse.leap { background: var(--amber); }
    .leap-line { position: absolute; width: 2px; background: var(--amber); }
    .rests { position: relative; height: 28px; }
    .rest {
      position: absolute; top: 4px; height: 18px; overflow: hidden; white-space: nowrap;
      border: 1px dashed rgba(46, 230, 214, .7); color: var(--cyan); font-size: 10px;
      line-height: 16px; padding: 0 4px; border-radius: 4px;
    }
    .pad { height: 6px; background: #8eb4ff; }
    .pad-staff { position: relative; height: 180px; }
    .legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: .75rem; }
    .swatch { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
    .chapter { margin-top: 36px; }
    .cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    .card { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: rgba(16, 24, 44, .7); }
    .card ul { margin: 0 0 8px; padding-left: 16px; }
    .flow { display: flex; flex-wrap: wrap; gap: 8px; padding: 0; margin: 0; list-style: none; }
    .flow li { border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; font-size: .78rem; }
    .table-scroll { overflow-x: auto; max-width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    th, td { text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); vertical-align: top; }
    video { border-radius: 12px; margin-top: 8px; }
    @media (max-width: 800px) {
      .intro, .bench, .cards { grid-template-columns: 1fr; }
      .index { flex-direction: row; overflow-x: auto; }
      .index button { flex: 0 0 auto; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <p class="kicker">Synthwave Basslines</p>
      <div class="horizon"></div>
      <div class="intro">
        <div>
          <h1 id="title">Gate Pulse</h1>
          <p class="lede" id="identity"></p>
          <p class="meta" id="facts"></p>
          <p id="rhythm"></p>
          <p id="harmony"></p>
          <p class="note" id="limits"></p>
          <p class="note" id="departures"></p>
          <p><a href="media.html">Stills</a> · <a href="midi/arrangement.mid">Arrangement</a> · <a href="#files">Files</a></p>
        </div>
        <figure class="hero">
          <img src="art/hero.jpg" width="1280" height="720" alt="Illustration of a neon night road with cyan bass pulses and amber octave peaks. Not a photograph of a studio or of performers.">
          <figcaption>Illustration of a neon night road. Not a photograph of a recording session or of performers.</figcaption>
        </figure>
      </div>
    </header>
    <section class="chapter" id="roll">
      <div class="bench">
        <div>
          <p class="kicker">Eight studies</p>
          <div class="index" id="index"></div>
        </div>
        <div>
          <div class="switch">
            <button type="button" id="var-a" aria-pressed="true">Variation A</button>
            <button type="button" id="var-b" aria-pressed="false">Variation B</button>
            <button type="button" id="play">Play bass</button>
            <button type="button" id="pad-toggle" aria-pressed="false">Harmonic reference</button>
          </div>
          <p class="note" id="keys">Space plays the bass. J and K change study.</p>
          <div class="phrases" id="phrases"></div>
          <div class="system">
            <div class="axis" id="axis"></div>
            <div class="scroller" id="scroller">
              <div class="bars" id="bars"></div>
              <div class="staff" id="bass-staff"></div>
              <div class="rests" id="rest-row"></div>
            </div>
          </div>
          <p class="legend">
            <span><i class="swatch" style="background:#2ee6d6"></i>bass pulse</span>
            <span><i class="swatch" style="background:#ffb454"></i>octave leap</span>
            <span><i class="swatch" style="background:transparent;border:1px dashed #2ee6d6"></i>rest of an eighth or longer</span>
          </p>
          <p class="note" id="status">Reading the MIDI.</p>
          <div id="pad-panel" hidden>
            <h2>Harmonic reference</h2>
            <p class="note">Separate MIDI file. These notes are not drawn on the bass staff and are not merged into the bass part.</p>
            <div class="pad-scroll"><div class="pad-staff" id="pad-staff"></div></div>
          </div>
        </div>
      </div>
    </section>
    <section class="chapter">
      <h2>Studies</h2>
      <p>__RANGE__</p>
      <ul>__STUDIES__</ul>
    </section>
    <section class="chapter">
      <h2>File contract</h2>
      <ol class="flow">
        <li>Canonical score</li>
        <li>MIDI</li>
        <li>Reopened validation</li>
        <li>MP3</li>
        <li>Film</li>
        <li>Stills</li>
        <li>Drafts</li>
        <li>This page</li>
      </ol>
    </section>
    <section class="chapter" id="map">
      <h2>Set map</h2>
      <div class="cards">__MAP__</div>
    </section>
    <section class="chapter" id="files">
      <h2>Files</h2>
      <p class="meta">Validation __RESULT__. Core __CORE__. Harmonic references __REFS__. <a href="midi/validation-Cursor.json">validation report</a> · <a href="catalog/catalog-Cursor.json">catalog</a> · <a href="score/canonical-score-Cursor.json">canonical score</a></p>
      <p>__WARNING__</p>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Part</th><th>Role</th><th>Var</th><th>Count</th><th>BPM</th><th>Bars</th><th>Notes</th></tr></thead>
          <tbody>__ROWS__</tbody>
        </table>
      </div>
    </section>
    <section class="chapter" id="reading">
      <p class="kicker">Recorded reading</p>
      <h2>Study 01, variation A, all 8 bars</h2>
      <p>This MP3 is __SECONDS__ seconds. __PREVIEW_LINE__. It includes bass A and harmonic reference A from study 01. The film is __FILM_SECONDS__ seconds and shows __ON_PICTURE__.</p>
      <audio controls preload="metadata" src="preview/preview.mp3"></audio>
      <p><a href="preview/preview.mp3">preview/preview.mp3</a> · <a href="preview/preview-manifest-Cursor.txt">preview manifest</a></p>
      <video controls preload="metadata" poster="film/poster.jpg" width="1280" height="720">
        <source src="film/preview.mp4" type="video/mp4">
        <track kind="captions" src="film/preview.vtt" srclang="en" label="English" default>
      </video>
      <p><a href="film/preview.mp4">film/preview.mp4</a> · <a href="film/preview.vtt">captions</a></p>
    </section>
    <section class="chapter">
      <h2>Validator</h2>
      <ul>__RULES__</ul>
      <p>__PROGRAM__</p>
      <p>__AUDITION__</p>
    </section>
    <section class="chapter">
      <h2>DRAFT article</h2>
      <p>__ARTICLE_TITLE__</p>
      <p>__TAG_LINE__</p>
      <p><a href="articles/medium-draft-Cursor.md">Article draft</a> · <a href="articles/medium-paste-Cursor.txt">plain text</a></p>
    </section>
    <p>__PUBLICATION__</p>
  </div>
  <script id="pack" type="application/json">__DATA__</script>
  <script>
    const pack = JSON.parse(document.getElementById("pack").textContent);
    const index = document.getElementById("index");
    const phrases = document.getElementById("phrases");
    const scroller = document.getElementById("scroller");
    const bars = document.getElementById("bars");
    const staff = document.getElementById("bass-staff");
    const restRow = document.getElementById("rest-row");
    const axis = document.getElementById("axis");
    const padPanel = document.getElementById("pad-panel");
    const padStaff = document.getElementById("pad-staff");
    const status = document.getElementById("status");
    const STAFF_H = 392;
    const PAD_H = 180;
    let studyId = "s01";
    let variation = "a";
    let bassNotes = [];
    let padNotes = [];
    let showPad = false;
    let audio = null;
    let playing = false;
    let followId = 0;
    let rollWidth = 1200;

    function study() {
      return pack.studies.find((item) => item.id === studyId);
    }
    function pitchName(pitch) {
      return study().spell[pitch % 12] + (Math.floor(pitch / 12) - 1);
    }
    function yBass(pitch) {
      return 12 + (60 - pitch) * ((STAFF_H - 24) / 32);
    }
    function yPad(pitch) {
      return 10 + (84 - pitch) * ((PAD_H - 20) / 24);
    }
    function readVlq(view, offset) {
      let value = 0;
      let byte = 0;
      do {
        byte = view.getUint8(offset);
        offset += 1;
        value = (value << 7) | (byte & 0x7f);
      } while (byte & 0x80);
      return [value, offset];
    }
    function parseMidi(buffer) {
      const view = new DataView(buffer);
      if (String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3)) !== "MThd" || view.getUint16(12) !== 960) {
        throw new Error("unexpected MIDI header");
      }
      const tracks = view.getUint16(10);
      let offset = 14;
      const notes = [];
      for (let track = 0; track < tracks; track += 1) {
        if (String.fromCharCode(view.getUint8(offset), view.getUint8(offset + 1), view.getUint8(offset + 2), view.getUint8(offset + 3)) !== "MTrk") {
          throw new Error("missing track");
        }
        const length = view.getUint32(offset + 4);
        offset += 8;
        const end = offset + length;
        let tick = 0;
        let running = 0;
        const open = new Map();
        while (offset < end) {
          let delta;
          [delta, offset] = readVlq(view, offset);
          tick += delta;
          let byte = view.getUint8(offset);
          if (byte >= 0x80) {
            running = byte;
            offset += 1;
          }
          if (running === 0xff) {
            offset += 1;
            let metaLen;
            [metaLen, offset] = readVlq(view, offset);
            offset += metaLen;
            continue;
          }
          const kind = running & 0xf0;
          const data1 = byte < 0x80 ? byte : view.getUint8(offset);
          if (byte >= 0x80) offset += 1;
          let data2 = 0;
          if (kind !== 0xc0 && kind !== 0xd0) {
            data2 = view.getUint8(offset);
            offset += 1;
          }
          const key = (running & 0x0f) + ":" + data1;
          if (kind === 0x90 && data2 > 0) open.set(key, { tick: tick, velocity: data2 });
          else if (kind === 0x80 || (kind === 0x90 && data2 === 0)) {
            const started = open.get(key);
            if (started) {
              notes.push({ pitch: data1, start: started.tick, duration: tick - started.tick, velocity: started.velocity });
              open.delete(key);
            }
          }
        }
      }
      notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
      return notes;
    }
    function partPath(role) {
      const found = pack.parts.find((part) => part.study_id === studyId && part.role === role && part.variation === variation);
      if (!found) throw new Error("missing " + role);
      return found.path;
    }
    function renderCopy() {
      const item = study();
      document.getElementById("title").textContent = item.title;
      document.getElementById("identity").textContent = item.identity;
      document.getElementById("facts").textContent = item.id + " · " + item.bpm + " BPM · " + item.bars + " bars · " + (item.bars * 4 * 60 / item.bpm).toFixed(2) + " s · " + item.collection + " · tonic " + item.tonic;
      document.getElementById("rhythm").textContent = item.rhythm;
      document.getElementById("harmony").textContent = item.harmonic_rhythm + " " + item.accent;
      document.getElementById("limits").textContent = item.limitations;
      document.getElementById("departures").textContent = item.departures.length ? item.departures.join(" ") : "No pitch in this study is flagged as a departure.";
      document.getElementById("keys").textContent = item.title + " " + variation.toUpperCase() + ". Space plays the bass. J and K change study.";
      for (const button of index.querySelectorAll("button")) button.setAttribute("aria-pressed", button.dataset.id === studyId ? "true" : "false");
      document.getElementById("var-a").setAttribute("aria-pressed", variation === "a" ? "true" : "false");
      document.getElementById("var-b").setAttribute("aria-pressed", variation === "b" ? "true" : "false");
      phrases.innerHTML = "";
      item.phrases.forEach((phrase) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = phrase.name;
        button.addEventListener("click", () => {
          scroller.scrollTo({ left: Math.max(0, (phrase.start_bar / item.bars) * rollWidth - 12), behavior: "smooth" });
        });
        phrases.appendChild(button);
      });
    }
    function drawAxis() {
      axis.innerHTML = "";
      [60, 48, 36].forEach((pitch) => {
        const label = document.createElement("span");
        label.textContent = pitchName(pitch);
        label.style.top = yBass(pitch) + "px";
        axis.appendChild(label);
      });
    }
    function drawBass() {
      const item = study();
      const container = item.bars * 4 * 960;
      rollWidth = Math.max(scroller.clientWidth || 640, item.bars * 150);
      bars.style.width = rollWidth + "px";
      staff.style.width = rollWidth + "px";
      restRow.style.width = rollWidth + "px";
      bars.innerHTML = "";
      staff.innerHTML = "";
      restRow.innerHTML = "";
      let cursor = 0;
      item.changes.forEach((name, changeIndex) => {
        const span = item.change_bars[changeIndex];
        const mark = document.createElement("div");
        mark.className = "change";
        mark.textContent = name;
        mark.style.left = (cursor / item.bars) * rollWidth + "px";
        mark.style.width = Math.max(0, (span / item.bars) * rollWidth - 4) + "px";
        bars.appendChild(mark);
        cursor += span;
      });
      const leaps = new Set();
      bassNotes.forEach((note, noteIndex) => {
        const next = bassNotes[noteIndex + 1];
        if (next && Math.abs(next.pitch - note.pitch) >= 12) {
          leaps.add(noteIndex);
          leaps.add(noteIndex + 1);
        }
      });
      bassNotes.forEach((note, noteIndex) => {
        const block = document.createElement("div");
        block.className = "pulse" + (leaps.has(noteIndex) ? " leap" : "");
        block.title = pitchName(note.pitch) + " · velocity " + note.velocity;
        block.style.left = (note.start / container) * rollWidth + "px";
        block.style.width = Math.max(2, (note.duration / container) * rollWidth - 2) + "px";
        block.style.top = (yBass(note.pitch) - 4) + "px";
        staff.appendChild(block);
        const next = bassNotes[noteIndex + 1];
        if (!next || Math.abs(next.pitch - note.pitch) < 12) return;
        const gapStart = note.start + note.duration;
        const gap = next.start - gapStart;
        const gapPx = (gap / container) * rollWidth;
        if (gapPx < 4) return;
        const line = document.createElement("div");
        line.className = "leap-line";
        const y1 = yBass(note.pitch);
        const y2 = yBass(next.pitch);
        line.style.left = ((gapStart + next.start) / 2 / container) * rollWidth - 1 + "px";
        line.style.top = Math.min(y1, y2) + "px";
        line.style.height = Math.max(2, Math.abs(y2 - y1)) + "px";
        staff.appendChild(line);
      });
      const gaps = [];
      if (bassNotes.length && bassNotes[0].start >= 480) gaps.push([0, bassNotes[0].start]);
      for (let noteIndex = 0; noteIndex < bassNotes.length - 1; noteIndex += 1) {
        const end = bassNotes[noteIndex].start + bassNotes[noteIndex].duration;
        const nextStart = bassNotes[noteIndex + 1].start;
        if (nextStart - end >= 480) gaps.push([end, nextStart]);
      }
      if (bassNotes.length) {
        const end = bassNotes[bassNotes.length - 1].start + bassNotes[bassNotes.length - 1].duration;
        if (container - end >= 480) gaps.push([end, container]);
      }
      gaps.forEach((gap) => {
        const mark = document.createElement("div");
        mark.className = "rest";
        const width = Math.max(0, ((gap[1] - gap[0]) / container) * rollWidth - 3);
        mark.style.left = (gap[0] / container) * rollWidth + "px";
        mark.style.width = width + "px";
        mark.textContent = width >= 36 ? "rest" : "";
        mark.title = "rest";
        restRow.appendChild(mark);
      });
      drawAxis();
      const leapCount = leaps.size ? bassNotes.filter((note, noteIndex) => leaps.has(noteIndex) && bassNotes[noteIndex - 1] && Math.abs(note.pitch - bassNotes[noteIndex - 1].pitch) >= 12).length : 0;
      status.dataset.bass = String(bassNotes.length);
      status.dataset.leaps = String(leapCount);
      status.dataset.rests = String(gaps.length);
      status.dataset.pads = String(padNotes.length);
      status.textContent = bassNotes.length + " bass notes from " + partPath("bass") + ". " + leapCount + " octave leaps. " + gaps.length + " rests. Harmonic reference is " + (showPad ? "in its own lane." : "hidden.");
    }
    function drawPads() {
      const item = study();
      const container = item.bars * 4 * 960;
      padStaff.style.width = rollWidth + "px";
      padStaff.innerHTML = "";
      if (!showPad) return;
      padNotes.forEach((note) => {
        const block = document.createElement("div");
        block.className = "pad";
        block.title = pitchName(note.pitch);
        block.style.left = (note.start / container) * rollWidth + "px";
        block.style.width = Math.max(2, (note.duration / container) * rollWidth - 2) + "px";
        block.style.top = (yPad(note.pitch) - 3) + "px";
        padStaff.appendChild(block);
      });
    }
    async function loadStudy() {
      stopPlayback();
      renderCopy();
      status.textContent = "Reading the MIDI.";
      try {
        const bassRes = await fetch(partPath("bass"));
        const padRes = await fetch(partPath("harmonic-reference"));
        if (!bassRes.ok || !padRes.ok) throw new Error("MIDI request failed");
        bassNotes = parseMidi(await bassRes.arrayBuffer());
        padNotes = parseMidi(await padRes.arrayBuffer());
        drawBass();
        drawPads();
      } catch (error) {
        bassNotes = [];
        padNotes = [];
        status.textContent = "The MIDI did not load. " + error.message;
      }
    }
    function freq(pitch) {
      return 440 * Math.pow(2, (pitch - 69) / 12);
    }
    function schedule(ctx, note, origin, amount, type) {
      const item = study();
      const seconds = (tick) => tick / 960 * item.tempo_us / 1000000;
      const when = origin + seconds(note.start);
      const duration = Math.max(0.05, seconds(note.duration));
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.value = freq(note.pitch);
      const level = amount * (note.velocity / 110);
      const attack = Math.min(0.012, duration * 0.2);
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, level), when + attack);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(when);
      osc.stop(when + duration + 0.02);
    }
    function stopPlayback() {
      playing = false;
      cancelAnimationFrame(followId);
      if (audio) audio.close();
      audio = null;
      document.getElementById("play").textContent = "Play bass";
    }
    function playBass() {
      if (!bassNotes.length) return;
      stopPlayback();
      const ctx = new AudioContext();
      audio = ctx;
      playing = true;
      document.getElementById("play").textContent = "Stop";
      const origin = ctx.currentTime + 0.05;
      bassNotes.forEach((note) => schedule(ctx, note, origin, 0.08, "sawtooth"));
      if (showPad) padNotes.forEach((note) => schedule(ctx, note, origin, 0.03, "triangle"));
      const item = study();
      const container = item.bars * 4 * 60 / item.bpm;
      const follow = () => {
        if (!playing || !audio) return;
        if (audio.currentTime - origin < container) followId = requestAnimationFrame(follow);
        else stopPlayback();
      };
      follow();
    }
    function stepStudy(direction) {
      const current = pack.studies.findIndex((item) => item.id === studyId);
      studyId = pack.studies[(current + direction + pack.studies.length) % pack.studies.length].id;
      loadStudy();
    }
    pack.studies.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.id = item.id;
      button.textContent = item.id.slice(1) + " " + item.title;
      button.addEventListener("click", () => { studyId = item.id; loadStudy(); });
      index.appendChild(button);
    });
    document.getElementById("var-a").addEventListener("click", () => { variation = "a"; loadStudy(); });
    document.getElementById("var-b").addEventListener("click", () => { variation = "b"; loadStudy(); });
    document.getElementById("play").addEventListener("click", () => { if (playing) stopPlayback(); else playBass(); });
    document.getElementById("pad-toggle").addEventListener("click", () => {
      showPad = !showPad;
      padPanel.hidden = !showPad;
      document.getElementById("pad-toggle").setAttribute("aria-pressed", showPad ? "true" : "false");
      if (bassNotes.length) {
        drawBass();
        drawPads();
      }
    });
    window.addEventListener("keydown", (event) => {
      const target = event.target;
      if (target && target.closest && target.closest("video, audio, input, textarea")) return;
      if (event.code === "Space") {
        event.preventDefault();
        if (playing) stopPlayback();
        else playBass();
      } else if (event.key === "j" || event.key === "J") stepStudy(-1);
      else if (event.key === "k" || event.key === "K") stepStudy(1);
    });
    loadStudy();
  </script>
</body>
</html>
"""
