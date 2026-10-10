# Demo video: script, storyboard and production guide

**Target length:** 2:40 (the hackathon requires 2–3 minutes). **Voiceover:** about 370 words at a relaxed ~140 words per minute. **Format:** 1920×1080, 30 fps, captions on.

## Running order

| Time | Segment | On screen | Source |
|---|---|---|---|
| 0:00–0:12 | Hook + title | Animated interference ripples; title "Phase Shift" fades in; subtitle "A quantum interference puzzle · Qiskit × IonQ × Qollab" | **Higgsfield** clip `title_card` (below) + text overlay in your editor |
| 0:12–0:25 | Who / what | Qollab project page, then press **Run** → *Select QPU* → IonQ simulator; the game loads | Screen recording |
| 0:25–1:20 | Live demo, level 1 | Invisible Ink: run with recombiner off at 0° and 90° (still 50/50) → switch on recombine → dial 180° → solved, goal meter, histogram table, arrows panel → **Confirm on IonQ** → 3 stars | Screen recording, with zoom-ins on the histogram and arrows |
| 1:20–1:40 | Levels 2 and 3 (montage) | Dark Port: one run says "Δ ≈ ±75°", second run is dark. Eraser: off = all 25%; on + 180° = disagree 100%; photon alone still 50% | Screen recording, sped up 1.5× |
| 1:40–2:10 | Under the hood | `levels.py` level definition → `circuits.build_circuit` → `paths.analyze` (classical vs quantum) → `api.run_level` sending one job to the injected IonQ `backend` | Code in the editor (large font) + **Higgsfield** clip `arrows_explainer` as a 4 s cut-in |
| 2:10–2:32 | Access and extend | Qollab page "How to run"; GitHub README; `docs/DEVELOPER_GUIDE.md` "Add a level" | Screen recording |
| 2:32–2:40 | Outro | End card: title, Qollab link, GitHub link, "MIT licensed · This effort is supported by Qollab & IonQ" | **Higgsfield** still `video_title_bg.png` + text |

## Storyboard and voiceover (exact text)

### 0:00–0:12 · Hook

*Screen:* animated ripples (Higgsfield `title_card`), the title appears at 0:03, the subtitle at 0:06.

> **VO:** "Quantum computers aren't just fancy dice. Their power comes from interference: possibilities that add up, or cancel out. Phase Shift is a puzzle game where you make that happen yourself."

### 0:12–0:25 · Who and what

*Screen:* the Qollab project page. Click **Run**, choose **IonQ simulator** in *Select QPU*. The game loads; zoom on "Quantum backend: … (IonQ)".

> **VO:** "We built it in Qiskit for the Qollab and IonQ hackathon. It runs right here on Qollab: practice runs use a simulator in your browser, and you confirm each solution on IonQ's simulator."

### 0:25–1:20 · Live demo: level 1, *Invisible Ink*

*Screen 0:25:* level 1. Point at the circuit strip: H, P(φ), the dashed "Recombine" slot. Goal: P(|1⟩) ≥ 90%.

> **VO:** "Level one. A Hadamard splits the qubit into two paths. I can paint a phase on the lower path, and I need to measure one at least ninety percent of the time."

*Screen 0:35:* run at φ = 0°: 50/50. Turn the dial to 90°, run: 50/50 again. The feedback reads "The phase is invisible!"

> **VO:** "Zero degrees: fifty-fifty. Ninety degrees: still fifty-fifty. The phase is real, but a measurement can't see it on its own."

*Screen 0:47:* switch **Recombine** on (zoom on the circuit: the dashed H becomes solid). Dial 180°, run. The goal meter fills, ★★ appears, and "You solved the level!"

> **VO:** "So I recombine the paths with a second Hadamard, and set the phase to one-eighty. One hundred percent."

*Screen 0:57:* scroll to **Follow the arrows**. Zoom on the |0⟩ card (blue and orange arrows opposite, sum = dot) and then on the |1⟩ card (arrows in line, long white sum).

> **VO:** "Here's why. Every path to an outcome carries an arrow. For zero, the two arrows point opposite ways and cancel. For one, they line up and add. Classically you'd expect fifty percent; the difference is interference."

*Screen 1:10:* press **Confirm on IonQ**. The status counts seconds, then shows "Done on IonQ …"; ★★★ appears and the button locks with "IonQ job used for this Run".

> **VO:** "Now I send this exact circuit to IonQ's simulator as one job. Confirmed: three stars."

### 1:20–1:40 · Levels 2 and 3

*Screen 1:20:* Dark Port (1.5× speed). Run at 0° → for example "Δ ≈ ±75°" (the mystery phase is random, so your numbers will differ). Turn the dial by that amount, run → dark, θ revealed.

> **VO:** "In Dark Port, a hidden phase sits on one path. The brightness tells you how far off you are, a second run tells you which way, and the detector goes dark."

*Screen 1:30:* Eraser. Eraser off: four bars at 25%. Eraser on, 180°: disagree 100%; highlight "photon alone: 50%".

> **VO:** "In the eraser level, a detector records which path was taken, and interference disappears until you erase that record. Then it returns, hidden in the correlations."

### 1:40–2:10 · Under the hood

*Screen 1:40:* editor, `phaseshift/levels.py`, the `INVISIBLE_INK` definition (steps, controls, target).

> **VO:** "Under the hood, each level is just data: gates, controls and a target."

*Screen 1:46:* `circuits.build_circuit`: `qc.h`, `qc.p`, `qc.measure`.

> **VO:** "Qiskit builds the circuit from your choices."

*Screen 1:51:* 4 s cut-in of the Higgsfield `arrows_explainer` clip, then `paths.analyze`: highlight `quantum = abs(total) ** 2` and `classical = sum(abs(a) ** 2 …)`.

> **VO:** "To explain the results, we enumerate every path through your circuit and compare the classical sum of probabilities with the quantum sum of arrows."

*Screen 2:01:* `api.run_level`: highlight `execution.submit(target, qc, shots=…)` and the IonQ guard.

> **VO:** "On Qollab, the IonQ backend is passed in, and each confirmation is one single-circuit job, compiled without re-optimising, so IonQ runs exactly what you built."

### 2:10–2:32 · Access and extend

*Screen 2:10:* Qollab project page, "How to run". Then the GitHub README and `docs/DEVELOPER_GUIDE.md` "Add a level".

> **VO:** "To play, open Phase Shift on Qollab, press Run and pick IonQ's simulator. Everything is MIT licensed. Adding a level means adding one level definition and a feedback function; the interface builds itself."

### 2:32–2:40 · Outro

*Screen:* end card over `video_title_bg.png`: "Phase Shift", Qollab and GitHub links, "MIT · This effort is supported by Qollab & IonQ".

> **VO:** "Phase Shift: make the probabilities interfere. Thanks for watching."

## Visual assets with Higgsfield MCP

Already generated (job ids in `assets/higgsfield_manifest.json`):

| Asset | Higgsfield job | Use |
|---|---|---|
| `video_title_bg.png` (16:9, 2k) | `3bf6ff00-58bb-49f2-9403-7f63f80f841b` | Outro still; start frame of the title clip |
| `video_arrows_explainer.png` (16:9, 2k) | `31b75364-e2ba-4787-8f80-07adc665dc8b` | Start frame of the arrows clip |
| `title_card` clip (5 s, 1280×720, Kling 3.0, silent) | `22a0aaad-f1fd-473f-811d-ed501b8a5b8b` | 0:00–0:12 (slow it to 50% or loop it) |
| `arrows_explainer` clip (5 s, 1280×720, Kling 3.0, silent) | `7b490f88-644a-4d36-a287-a00fec3cce48` | 1:51 cut-in |

Download them from your Higgsfield library, or run `python tools/embed_art.py`, which also saves the clips to `assets/video/`. The clips are 720p: place them on a 1080p timeline scaled to fill (they are soft, abstract backgrounds, so the upscale is not noticeable), or upscale them with Higgsfield's `upscale_video`.

To regenerate or add clips, ask your assistant to call the Higgsfield MCP tools like this:

```text
generate_image  model="recraft_v4_1"  aspect_ratio="16:9"  resolution="2k"  model_type="standard"
                colors=["#0B1020","#141B34","#4EA8FF","#FFB000","#5CE1E6"]  background_color="#0B1020"
                prompt="<prompt from assets/higgsfield_manifest.json>"

generate_video  model="kling3_0"  duration=5  mode="std"  sound="off"  aspect_ratio="16:9"
                medias=[{value: "<image job id>", role: "start_image"}]
                prompt="Slow gentle camera push-in on the glowing interference ripples; the cyan and orange
                        ripple rings pulse softly outward and the bright and dark fringes shimmer; the qubit
                        orb at the centre breathes with light. Calm, elegant, no text, no new objects."
```

Tips: preflight the cost with `get_cost: true` (about 1.25 credits per Recraft image and 7.5 per 5 s Kling clip at the time of writing); always ask for "no text" and add titles in your editor, where the text stays crisp and is easy to change; keep the palette above so the clips match the game.

Optional extra clips, if you have time:
* **Two-path B-roll** (Kling 3.0, start image `hero_banner.png` job `175abc8b-a0dc-457e-936b-bce206ede59f`): "light travels along the blue and orange paths and meets at the second crystal; ripples bloom".
* **Detector going dark** (start image `level2_dark_port.png` job `77b5db44-1e73-4071-9cf1-d41e3bf134ff`): "the bright detector slowly dims to black while the other glows".

## Recording and editing

**Screen recording**

* **OBS Studio** (free, Windows/macOS/Linux): Display Capture or Window Capture of the browser, 1920×1080, 30 fps, MKV (remux to MP4 afterwards). Alternatives: Windows **Win+Alt+R** (Xbox Game Bar), macOS **Cmd+Shift+5**, or Loom.
* Before recording: browser zoom 125% so text is readable on video; hide bookmarks and extensions; use a fresh profile (or clear the `phase-shift:v1` localStorage key) so level 1 starts unsolved; do one IonQ dry run, then **Stop/Run** so the take has a fresh IonQ job.
* Record each segment as its own take; it is easier to cut than to redo everything.

**Voiceover**

* Read the VO lines above into a USB or phone microphone in a quiet room (Audacity or the phone's voice memo app). Apply noise reduction and normalise to about −16 LUFS.
* Or have Higgsfield generate the narration (`generate_audio` with a text-to-speech model), then check that the timing matches the screen.

**Editing** (free: DaVinci Resolve, CapCut, Clipchamp, iMovie, Shotcut)

1. Lay the voiceover on the timeline first, then cut the screen takes to it.
2. Put the Higgsfield `title_card` clip under 0:00–0:12 and add the title text; use the `arrows_explainer` clip as a 4 s cut-in at 1:51.
3. Zoom (Ken Burns / transform) on the histogram and the arrows at 0:57.
4. Add burned-in captions (Resolve/CapCut auto-captions, then correct "Qiskit", "IonQ", "Qollab", "Hadamard").
5. Optional quiet background music: the Qollab hackathon soundtrack, if its terms allow reuse, or a royalty-free track at −28 dB under the voice.
6. Export H.264 MP4, 1080p, 30 fps, about 8–12 Mbps. Check the length is between 2:00 and 3:00.

## Publishing (must be viewable without signing in)

1. Upload to **YouTube** → *Create → Upload video*. Title: "Phase Shift: a quantum interference puzzle (Qollab × IonQ Hackathon 2026)".
2. Description: a two-line summary, the Qollab project link, the GitHub link, "MIT licensed", and "This effort is supported by Qollab & IonQ."
3. Audience: "No, it's not made for kids". Visibility: **Unlisted** (anyone with the link can watch, no sign-in) or **Public**. Do **not** choose Private.
4. Under *Subtitles*, upload or confirm the captions.
5. Open the link in a private/incognito window to confirm it plays without signing in.
6. Paste the link into the Qollab project page ("Demo video"), the README (top) and the hackathon submission form on your team page.
