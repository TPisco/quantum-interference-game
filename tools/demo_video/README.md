# Demo video tooling

Reproducible edit of the 2–3 minute hackathon demo video, built with Higgsfield MCP:

* **Voiceover:** Higgsfield TTS (`seed_audio`, preset voice "Julian"), one file per segment (text in `edl.json`).
* **Title / explainer clips:** Higgsfield images (Recraft V4.1) animated with Kling 3.0 (see `assets/higgsfield_manifest.json`).
* **Edit:** `render.py` turns `edl.json` into the finished MP4 with ffmpeg. It was run in Higgsfield's cloud sandbox.

```bash
python3 vo_clean.py raw_vo/ vo/            # trim ends, shorten TTS pauses > 0.7 s
SRC_DIR=recordings ASSET_DIR=assets VO_DIR=vo OUT_DIR=out \
  python3 render.py edl.json --work work [--reuse] [--only s03,s04] [--segments-only]
```

`edl.json` lists 17 segments. Each **clip** segment picks ranges of a screen recording
(`ranges`, with optional `freeze` frames), eased zooms or a camera `path` (in source
time), privacy `blur` boxes, and labels. **Card** segments put title text over a Higgsfield
clip or image. Every segment is timed to its voiceover: ranges speed up or slow down
together (0.6–3×) and freeze frames absorb the rest. Captions are written from the
authored text, timed with Whisper word timestamps when `faster-whisper` is available,
and burned in. Loudness is normalised to −16 LUFS.

Inputs not in the repo: the screen recordings and the Higgsfield media.

**Two cuts.** `edl.json` is the first cut, made from five recordings of the original
three-level game (`RunApp.mp4`, `level1.mp4`, `level2-3.mp4`, `readmeAndDevGuide.mp4`,
`levelPy.mp4`). The second cut covers the redesigned game (start page, five puzzles,
phone layout). Its voice is finished and the screen is recorded to fit it, following the
cue sheet in `docs/VIDEO_SCRIPT.md`:

```bash
ffmpeg -i bb0bbca9.wav -af "atrim=3.80:8.95,asetpts=PTS-STARTPTS" raw/s03c.wav  # s03c: the usable part of take bb0bbca9
python3 vo_clean.py raw/ clean/ 0.55 0.42                                # 17 TTS lines
python3 assemble.py script_v2.json clean/ phase_shift_vo_v2.wav 0.4 0.8 2.0 # 2:55.6 + timing sheet
python3 make_captions.py script_v2.json clean/ captions_v2.srt 0.4 0.8     # needs faster-whisper
```

* `script_v2.json`: the 17 lines (caption text and spoken text).
* `captions_v2.srt`: the captions, timed to the finished track.
* `clips/make_frames.py`: SVG keyframes for the Higgsfield clips, drawn in the game's style;
  `clips/render_svg.mjs` renders them to PNG with Playwright.
* `clips/arrows_anim.py`: the exact "arrows add or cancel" clip (Kling drew the sum wrong).
* `clips/fix_hook.py`: repaints the phase needle on the Kling hook clip and upscales it to 1080p.

`edl_v2.json` is written once the new recordings (`01_start.mp4` … `08_code.mp4`) exist,
because cut points and zoom boxes are measured on the real footage.
