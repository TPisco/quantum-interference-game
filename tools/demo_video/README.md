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
phone layout). Its voiceover is in `script_v2.json` and its shot list in
`docs/VIDEO_SCRIPT.md`; `edl_v2.json` is written once the new recordings
(`01_start.mp4` … `08_docs.mp4`) exist, because cut points and zoom boxes are measured
on the real footage.
