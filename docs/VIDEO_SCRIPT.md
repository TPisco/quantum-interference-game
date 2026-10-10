# Demo video: script, shot list and production guide

**Target length:** about 2:45 (the hackathon requires 2 to 3 minutes). **Voiceover:** about 360 words, read by Higgsfield text-to-speech (voice "Julian"). **Format:** 1920×1080, 30 fps, burned-in captions.

This is the second cut. It follows the redesigned game: the start page with its live interferometer, five puzzles (two of them new), and the phone layout. The voiceover text is also kept in machine-readable form in [`tools/demo_video/script_v2.json`](../tools/demo_video/script_v2.json), which is what the Higgsfield voice is generated from.

## Running order

| Time | Segment | On screen | Source |
|---|---|---|---|
| 0:00–0:10 | Hook and title | Interference ripples; "Phase Shift" title | Higgsfield clip `title_card` + title text |
| 0:10–0:26 | Start page | Qollab: Run, *Select QPU*, IonQ simulator; the start page and its live dial | `01_start.mp4` |
| 0:26–0:57 | Level 1, Invisible Ink | Phase alone gives 50/50; recombine; 180° solves; arrows; Confirm on IonQ | `02_level1.mp4` |
| 0:57–1:11 | Levels 2 and 3 | Dark Port goes dark; the eraser restores interference | `03_levels23.mp4`, sped up |
| 1:11–1:33 | Level 4, Kickback (new) | Flip off: the phase vanishes. Flip on: the control reads 1, the target stays 1 | `04_kickback.mp4` |
| 1:33–1:56 | Level 5, Amplifier (new) | Diffuser off: 25% each. On, 180°: \|11⟩ at 100%; four arrows aligned | `05_amplifier.mp4` |
| 1:56–2:11 | Under the hood | `levels.py`, `circuits.py`, `paths.py`, `api.py`; 3 s arrows cut-in | `06_code.mp4` + Higgsfield clip `arrows_explainer` |
| 2:11–2:23 | Phone and accessibility | Phone layout, sticky Run bar, keyboard focus | `07_mobile.mp4` |
| 2:23–2:33 | Open source | README, developer guide "Add a level" | `08_docs.mp4` |
| 2:33–2:42 | Outro | End card with links | Higgsfield still `video_title_bg.png` + text |

## Shot list: what to record

Record each file as its own take; extra seconds at the start and end are fine, they get trimmed. Keep the mouse still while the voice is explaining something, and move it slowly when you point at things.

**Before recording**

* Browser at 1920×1080, full screen (F11) so the taskbar and other tabs are not visible. Browser zoom 110% to 125%.
* Start with fresh progress: open DevTools, then *Application → Local storage* and delete the key `phase-shift:v1`, or use a new browser profile.
* Do one IonQ confirmation as a dry run, then press **Stop** and **Run** again, so each take that confirms on IonQ has a fresh IonQ job.
* If your Qollab username or avatar is visible, that is fine: the edit blurs those corners. Tell me where they are if they move.

| File | Length | What to do |
|---|---|---|
| `01_start.mp4` | 40 s | On the Qollab project page press **Run**, choose **IonQ simulator** in *Select QPU*. When the start page appears, do not touch anything for 3 s (the dial sweeps from 0° to 180° by itself). Then drag the demo dial slowly from 180° down to 0°, then to 90°. Scroll down to "Five puzzles" and back up. Click **Start level 1**. |
| `02_level1.mp4` | 60 s | Level 1, recombine off. Press **Run simulation** at 0°. Set 90°, run again. Switch **Recombine** on, set 180°, run. Scroll the results to the arrow cards for \|0⟩ and \|1⟩ and pause 3 s. Scroll back, press **Confirm on IonQ**, and wait for the result and the three stars. |
| `03_levels23.mp4` | 60 s | Click **Next**. Dark Port: run at 0°, read the "Δ ≈ ±…" hint, turn the dial by that much, run; if it got brighter, go the other way; stop when it is dark. Click **Next**. Eraser: run once with the eraser off; switch it on, set 180°, run; scroll to "Each qubit on its own". |
| `04_kickback.mp4` | 40 s | Click **Next**. Kickback: set 180° and run with **Flip** off ("Your phase vanished."). Switch **Flip** on, run ("Kicked back!"). Scroll to "Each qubit on its own" (target at 100%) and to the arrow cards. |
| `05_amplifier.mp4` | 40 s | Click **Next**. Amplifier: set 180°, run with the **Diffuser** off (four bars at 25%). Switch the diffuser on, run (\|11⟩ at 100%). Scroll to the arrow cards and pause on \|11⟩. |
| `06_code.mp4` | 30 s | In your editor (font size 18 to 20): `phaseshift/levels.py` at `KICKBACK`, `phaseshift/circuits.py` at `diffuser_gate`, `phaseshift/paths.py` at the two lines `quantum = …` and `classical = …`, `phaseshift/api.py` at the IonQ guard in `run_level`. About 6 s each. |
| `07_mobile.mp4` | 20 s | Chrome DevTools device toolbar (iPhone 14 Pro, 390 × 844), or a real phone. Start page, scroll a little, **Start level 1**, turn the dial, press **Run** in the bar at the bottom, then **View results**. |
| `08_docs.mp4` | 20 s | The GitHub README: scroll past the screenshots and the five-level table. Then open `docs/DEVELOPER_GUIDE.md` at "Add a level". |

## Voiceover (exact text)

Numbers are written as words in the spoken version so the voice reads them naturally; the captions use digits.

**s01 · 0:00 · Hook** (over the `title_card` clip)
> Quantum computers aren't just fancy dice. Their power comes from interference: possibilities that add up, or cancel out. Phase Shift lets you make that happen.

**s02 · 0:10 · Start page** (`01_start.mp4`)
> It runs right here on Qollab. Press Run, pick IonQ's simulator, and the start page opens with a live interferometer. Turn the phase and watch the arrows: aligned, detector 1 lights up; opposite, it goes dark.

**s03 · 0:26 · Level 1** (`02_level1.mp4`)
> Level 1. A Hadamard splits the qubit into two paths, and I paint a phase on the lower one. 0°: 50/50. 90°: still 50/50. A measurement can't see a phase on its own. So I recombine the paths with a second Hadamard and set 180°. 100%. The arrows show why: on 0 they cancel, on 1 they line up. Then I confirm this exact circuit on IonQ's simulator. Three stars.

**s04 · 0:57 · Levels 2 and 3** (`03_levels23.mp4`, 1.5× to 2×)
> In Dark Port, a detector's brightness tells you how far you are from a hidden phase. In the eraser level, a which-path detector kills interference until you erase what it knows.

**s05 · 1:11 · Level 4, Kickback** (`04_kickback.mp4`)
> Level 4 is new: Kickback. My phase gate now sits on a second qubit, and fires only when both are 1. With the target at 0, the phase vanishes. Flip the target with an X, and the phase kicks back onto the control. The target never changes. That's the trick inside Shor's algorithm.

**s06 · 1:33 · Level 5, Amplifier** (`05_amplifier.mp4`)
> Level 5, Amplifier, is Grover search. Four doors, the prize behind 11. Marking it with a phase alone changes nothing: every door stays at 25%. Switch on the diffuser, which reflects every amplitude about the average, and set the mark to 180°. One query, 100%. Four arrows line up on the prize.

**s07 · 1:56 · Under the hood** (`06_code.mp4`, with the `arrows_explainer` clip as a 3 s cut-in)
> Under the hood, each level is plain data. Qiskit builds your circuit, and an exact path sum draws every arrow. IonQ receives it compiled without re-optimising, so it runs exactly what you built.

**s08 · 2:11 · Phone and accessibility** (`07_mobile.mp4`)
> It works on a phone, with Run always under your thumb, and it's fully keyboard and screen-reader accessible: every chart is also a table.

**s09 · 2:23 · Open source** (`08_docs.mp4`)
> It's all MIT licensed. To add a puzzle, describe it in levels.py and write one feedback function. The interface builds itself.

**s10 · 2:33 · Outro** (end card over `video_title_bg.png`: "Phase Shift", "Make the probabilities interfere.", the Qollab and GitHub links, "MIT licensed · This effort is supported by Qollab & IonQ")
> Phase Shift. Make the probabilities interfere. Thanks for watching!

## Editing plan

* **Zooms** (eased, at most 1.7×): the start-page dial and its two detector cards (s02); the circuit and the Recombine switch, then the arrow cards (s03); the "Your phase vanished" feedback and the per-qubit table (s05); the \|11⟩ arrow card (s06); the code lines named in the shot list (s07).
* **Labels** (top right, two lines, cyan kicker plus white title): "RUNS ON QOLLAB / IonQ simulator" (s02), "LEVEL 1 / Invisible Ink" (s03), "LEVELS 2 AND 3 / Dark Port, Which-Path Eraser" (s04), "NEW / Level 4: Kickback" (s05), "NEW / Level 5: Amplifier" (s06), "UNDER THE HOOD / Qiskit + exact path sum" (s07), "RESPONSIVE / Phone layout, keyboard, screen reader" (s08), "OPEN SOURCE / MIT" (s09).
* **Speed:** the voice sets the pace. Recordings are sped up or slowed down per segment (0.6× to 3×) and freeze frames fill any gap, so do not worry about matching the timing while recording.
* **Privacy:** blur the Qollab account corner and anything personal in the first seconds of `01_start.mp4`.
* **Captions:** burned in from the caption text above, timed to the voice.
* **Audio:** voice normalised to −16 LUFS; no music needed.

`tools/demo_video/render.py` performs all of this from an edit decision list. After the recordings arrive, `tools/demo_video/edl_v2.json` will set the cut points, zoom boxes and blur boxes measured on the actual footage.

## Visual assets with Higgsfield MCP

Already generated (job ids in `assets/higgsfield_manifest.json`):

| Asset | Higgsfield job | Use |
|---|---|---|
| `video_title_bg.png` (16:9, 2k) | `3bf6ff00-58bb-49f2-9403-7f63f80f841b` | Outro still; start frame of the title clip |
| `video_arrows_explainer.png` (16:9, 2k) | `31b75364-e2ba-4787-8f80-07adc665dc8b` | Start frame of the arrows clip |
| `title_card` clip (5 s, 1280×720, Kling 3.0, silent) | `22a0aaad-f1fd-473f-811d-ed501b8a5b8b` | s01 (slowed to fill 10 s) |
| `arrows_explainer` clip (5 s, 1280×720, Kling 3.0, silent) | `7b490f88-644a-4d36-a287-a00fec3cce48` | s07 cut-in |

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

generate_audio  model="seed_audio"  voice_id="95429266-c0ac-4137-a209-63b8812b0f23"   (Julian)
                prompt="<the 'tts' text of one segment in tools/demo_video/script_v2.json>"
```

Preflight costs with `get_cost: true`. Ask for "no text" in image and video prompts and add titles in the edit, where they stay crisp. Generate voice segments in waves of at most three (the API rate-limits bursts), then run `tools/demo_video/vo_clean.py` to shorten any long pauses the voice leaves inside a sentence.

## Recording your own voice instead

Read the voiceover above into a USB or phone microphone in a quiet room, one file per segment (`s01.wav` … `s10.wav`), then run `vo_clean.py` on them. The edit works the same way.

## Publishing (must be viewable without signing in)

1. Upload to **YouTube**: *Create → Upload video*. Title: "Phase Shift: a quantum interference puzzle (Qollab × IonQ Hackathon 2026)".
2. Description: a two-line summary, the Qollab project link, the GitHub link, "MIT licensed", and "This effort is supported by Qollab & IonQ."
3. Audience: "No, it's not made for kids". Visibility: **Unlisted** (anyone with the link can watch, no sign-in) or **Public**. Do **not** choose Private.
4. Open the link in a private window to confirm it plays without signing in.
5. Paste the link into the Qollab project page ("Demo video"), the README (top) and the hackathon submission form.
