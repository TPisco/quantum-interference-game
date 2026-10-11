# Demo video: voiceover, shot list and Higgsfield assets

**Length:** 2:55.6 (the hackathon requires 2 to 3 minutes). **Voice:** Higgsfield text-to-speech, voice "Julian", 402 words in 17 lines. **Format:** 1920×1080, 30 fps, burned-in captions, voice at −16 LUFS.

This is the second cut. It shows the redesigned game: the start page with its live interferometer, five puzzles (two of them new), Confirm on IonQ, and the phone layout. The voiceover is finished; you record the screen to fit it. The text is also in [`tools/demo_video/script_v2.json`](../tools/demo_video/script_v2.json) and the timed captions in [`tools/demo_video/captions_v2.srt`](../tools/demo_video/captions_v2.srt).

## Download

Everything is on Higgsfield's CDN (no sign-in needed):

| What | Link | Details |
|---|---|---|
| **Everything in one zip** | [phase_shift_video_kit_v2.zip](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/e9963e2f-835f-46d6-8499-b3bd299adf72.zip) | 56 MB: full voice (WAV + MP3), the 17 lines as separate WAVs, captions (.srt), timing sheet, the 4 clips and the outro still, README |
| Full voiceover | [phase_shift_vo_v2.mp3](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/7c31f795-a5aa-4421-997f-0f6c7a22453c.mp3) | 2:55.6, 192 kbps (the 48 kHz WAV is in the zip) |
| Clip 1: hook | [01_hook_1080.mp4](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/64605ade-2d92-41b3-816c-a450eb7ff774.mp4) | 10 s, 24 fps, silent. The start-page interferometer: the dial turns 90° to 180° (5.0 to 7.4 s), the upper detector goes dark, the lower one lights up |
| Clip 2: arrows | [02_arrows_1080.mp4](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/301575dc-faff-42d6-ab3f-c56e62e017ec.mp4) | 6 s, 30 fps, silent. Left dial: the arrows line up and the white sum grows. Right dial: they turn opposite and the sum shrinks to a ring. Swing at 0.6 to 4.4 s |
| Clip 3: Kickback | [03_kickback_1080.mp4](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/5973ec40-9f3b-4faa-aeb0-43d80d59d5fb.mp4) | 5 s, 24 fps, silent. The level 4 emblem: the target wire stays steady while the phase kicks back and the control node lights up |
| Clip 4: Amplifier | [04_amplifier_1080.mp4](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/8b31ca4d-f9c0-4962-94d3-d3e4ab93c37f.mp4) | 5 s, 24 fps, silent. The level 5 emblem: four equal bars, then three sink and the marked one rises |
| Outro still | [05_outro_bg_1080.png](https://d2ol7oe51mr4n9.cloudfront.net/user_3HP5aHvMkn2ykh0zkqgQ1Jb9kuf/1e7d7e5d-332c-4340-b242-0b9851ad01fa.png) | Last frame of the hook; the lower half is empty for the end-card text |

All clips are 1920×1080 H.264. How they were made, and how to make new ones, is under [Higgsfield assets](#higgsfield-assets).

## Running order (measured on the finished voice)

Times are positions in the full voice track. Each row runs until the next one starts.

| Start | Line | On screen | Source |
|---|---|---|---|
| 0:00.0 | s01 Hook | Interferometer; title "Phase Shift" fades in over the empty lower half | **Clip 1** (trim its first 1.0 s so the detectors swap during "what makes a quantum computer more than a coin flip"), cut at 0:07.2 |
| 0:07.2 | s02 Runs on Qollab | Qollab: Run, Select QPU, IonQ simulator, Python loading | `01_start.mp4` |
| 0:14.8 | s03a The only rule | Start page fills in; the demo sweeps 0° to 180° | `01_start.mp4` |
| 0:17.0 | s03b Arrows add | Arrows add or cancel | **Clip 2** at 1×, cut back at 0:23.0 |
| 0:23.0 | s03c Lined up / opposite | The two detector cards of the demo | `01_start.mp4` |
| 0:28.5 | s04 Level 1 | 0°: 50/50. 180°: still 50/50 | `02_level1.mp4` |
| 0:49.0 | s05 Recombine | Recombine on: 100%; the arrow cards | `02_level1.mp4` |
| 1:08.4 | s06 Levels 2 and 3 | Dark Port and the Eraser, already solved | `03_levels23.mp4` |
| 1:22.6 | s07a New: Kickback | Kickback emblem | **Clip 3** at 1.6× (3.15 s, 1:22.56 to 1:25.72) so the slider drag in s07b stays on screen |
| 1:25.7 | s07b Kickback demo | Flip off: phase vanishes. Flip on: control reads 1 | `04_kickback.mp4` |
| 1:43.8 | s08a New: Amplifier | Amplifier emblem | **Clip 4** at 1×, hold the last frame 1 s |
| 1:49.8 | s08b Amplifier demo | 25% each; diffuser on: 100%; four arrows | `05_amplifier.mp4` |
| 2:06.4 | s09a Confirm on IonQ | Click Confirm on IonQ, job running | `05_amplifier.mp4` |
| 2:13.3 | s09b One job per Run | (IonQ wait cut out) result, three stars | `05_amplifier.mp4` |
| 2:23.2 | s10 Phone, accessibility | Phone layout; keyboard focus; aria-label | `06_mobile.mp4`, `07_keyboard.mp4`, `07c_inspect.mp4` |
| 2:32.5 | s11 Open source | Qiskit code panel; 207 tests; levels.py; five rows | `05_amplifier.mp4` tail, `08_code.mp4` |
| 2:47.7 | s12 Outro | End card | **Outro still** + text, holds to 2:55.6 |

The exact start and end of every line is in `timing_sheet.txt` in the zip; every caption is timed in `captions_v2.srt`.

## How to record

**The method.** Play one line's audio file (`voice_segments/sNN.wav` in the zip) in headphones and act on its cues below. Between lines, stop, set up the next state (scroll, framing) and start the next file; the editor cuts the pauses. Small timing slips are fine: footage is sped up or slowed down per line (0.6× to 3×) and freeze frames fill gaps.

**Session prep, once.**

* Chrome or Edge, 1920×1080, full screen (F11), browser zoom 100% (110% only if every framing check below still passes). OS "reduce motion" must be **off**, or the start-page sweep is skipped.
* Fresh progress: DevTools, *Application → Local storage →* the Qollab origin, delete the key `phase-shift:v1`, close DevTools, reload.
* **One Qollab Run covers takes 01 to 05 and 07.** Do not press Stop or reload until s09 is done, so the single IonQ job is still free in s09.
* Every time you drag a slider to 180°, check that the readout says **180° (π)**. If it shows 165° or 195°, click **+** or **−** once before you press Run.
* Blur the Qollab account corner (username, avatar) in the edit.

### `01_start.mp4` (s02, s03a, s03c; 15.4 s on screen, plus the loading wait and the hands-off stretch under Clip 2)

Start on the Phase Shift project page on Qollab, the Run button in view, the pointer beside it. It is fine to fall behind the voice in the dialog: the editor speeds it up. Hands off once Python starts loading; keep recording until the start page fills in.

| Line | Phrase | Action |
|---|---|---|
| s02 | "It runs on Qollab" | Pointer still beside Run |
| | "press Run" | Click **Run**; the *Select QPU* dialog opens |
| | "choose IonQ's simulator" | Pick the IonQ simulator, confirm the dialog |
| | "Qiskit starts in your browser" | Grey skeletons and the pill "Loading Python and Qiskit…". Hands off, keep rolling (the wait is cut) |
| s03a | "Here's the only rule you need" | The page fills in: "Start level 1" brightens from dimmed to full cyan (it is disabled while Python loads), the pill reads "Backend: … (IonQ)", and the demo slider sweeps 0° to 180° by itself (about 1.8 s). **Do not touch the demo**, or the sweep stops |
| s03b | (Clip 2 plays) | Keep recording hands-off underneath |
| s03c | "Lined up, a detector lights up" | Glide the pointer onto the **Detector \|1⟩** card: arrows aligned, long white sum, 100% |
| | "Opposite, they cancel: it goes dark" | Move to the **Detector \|0⟩** card: arrows opposite, small ring, 0%. Then glide onto "Start level 1" **without clicking** |

**Warm-up, off camera, right after take 01** (same Run, before take 02): click **Start level 1**, press **Run simulation** once (the first run loads Qiskit's simulator and is slow), scroll to **Reset puzzle** (in the row under the Run bar) and press it, then click **All puzzles**. The start button still reads "Start level 1".

### `02_level1.mp4` (s04, s05; 39.9 s)

Same Run. Level 1 opens at 0° with **Recombine** off (its gate dashed, tagged "off"). Use only **Run simulation** in this take: exactly three runs, so Level 1 ends on 2 stars and the IonQ job stays unused. Recovery: **Reset puzzle** (scroll under the Run bar), click **All puzzles**, then restart from s04. If Level 1 was already solved in the failed take, the button now reads "Continue level 1" and the stepper pill shows Level 1's stars (Reset puzzle keeps stars): click the button on "Level one, Invisible Ink" all the same, and crop or blur the button label and the stepper stars in the edit.

| Line | Phrase | Action |
|---|---|---|
| s04 | "Level one, Invisible Ink" | Click **Start level 1**; the play view fades in |
| | "A Hadamard splits the qubit into two paths" | Hover the H gate captioned "Split" |
| | "a phase turns the lower path's arrow" | Hover the P(φ) gate; on "arrow", move to **Run simulation** |
| | "I run it at zero degrees" | Click **Run simulation** (0°, Recombine off) |
| | "fifty-fifty" | Headline "The phase is invisible!", both bars near 50%. Move the pointer up onto the slider thumb (left end) |
| | "I turn it to one-eighty" | Drag to **180° (π)** |
| | "and run again" | Click **Run simulation** |
| | "still fifty-fifty" | Bars near 50/50 again; headline unchanged |
| | "measuring sees an arrow's length, not its direction" | Pointer still (editor zooms on the feedback text) |
| s05 | (in the pause) | Scroll so the switch "Recombine the paths (second H)" sits fully above the Run bar. Leave the dial at 180° |
| | "I switch on a second Hadamard" | Click the **Recombine** switch: the dashed H turns solid |
| | "Same phase, run" | Click **Run simulation** on the word "Same" (run 3) |
| | "one hundred percent" | "You solved the level!", two stars, "✓ met: 100.0%" |
| | "Why? Follow the arrows" | Scroll down until "Why? Follow the arrows" and both arrow cards are fully visible; circle the \|0⟩ card (arrows opposite) |
| | "Classical rules give fifty percent" | Pointer on the \|1⟩ card, row "Classical 50%" |
| | "quantum rules give one hundred" | On "Quantum 100%" |
| | "That difference is interference" | On "Interference +50%" |
| | "no coin flip can reach it" | Hold on the aligned arrows. End of take. **Never press Confirm on IonQ here** |

### `03_levels23.mp4` (s06; 14.2 s)

**Off camera first, same Run** (no Stop, no reload; use only Run simulation, never Reset):

1. Scroll up, click **Next: Dark Port**, run at 0°.
2. Read X from the feedback text "Turn φ by about X°" and round it to the nearest 15° (under "You're close." use the N in "Try adjusting the phase gate by N°").
3. Set φ to X and run. If the headline is not "Dark port! You solved the level.", set φ to 360° − X and run.
4. Click **Next: Which-Path Eraser**, switch on "Erase which-path info (H on detector)", set 180° (π), run: "Information erased. You solved the level!"
5. Click the **Invisible Ink** pill in the stepper and scroll to the top. Now start recording.

| Phrase | Action |
|---|---|
| "Dark Port hides a phase" | Click the **Dark Port** pill; its solved result reappears. Pointer on the "Mystery" gate |
| "how far you are from dark" | Pointer on "Dark port! You solved the level." and the \|1⟩ bar near 0% |
| "In the Eraser" | Click the **Which-Path Eraser** pill |
| "a spying detector kills the interference" | Pointer on the CNOT captioned "Detector" |
| "Erase what it knows" | Pointer on the Erase switch (on) and the H captioned "Eraser" |
| "only in the correlations" | Pointer on the histogram rows "photon 1 · detector 0" and "photon 0 · detector 1". End of take |

Editor: crop below the Results status line in this take (it keeps the last run's text when you switch pills).

### `04_kickback.mp4` (s07b; 18.1 s)

Before recording, click the **Kickback** pill and scroll so the circuit, the "Controlled phase φ" slider and the switch "Flip the target to \|1⟩ (X gate)" sit above the Run bar, with the results on the right (lower the browser zoom one step if they do not fit). Exactly two runs.

| Phrase | Action |
|---|---|
| "A controlled phase acts only when both qubits are one" | Hover the gate captioned "C-phase", then drag the slider to **180° (π)** |
| "With the target at zero" | Click **Run simulation** (Flip off) |
| "the phase vanishes" | Headline "Your phase vanished."; "control 0 · target 0" at 100% |
| "Flip the target with an X" | Click the **Flip** switch on; the X box turns solid |
| "and the phase kicks back onto the control" | Click **Run simulation** |
| "it reads one" | "Kicked back! You solved the level."; "control 1 · target 1" at 100% |
| "while the target stays one" | Scroll to "Each qubit on its own (ignoring the other)": target 100% |
| "phase estimation and Shor's algorithm" | Hold. End of take |

### `05_amplifier.mp4` (s08b, s09a, s09b, then a silent tail for s11; 33.3 s plus the IonQ wait)

Check first that the violet button still reads **Confirm on IonQ**. Click the **Amplifier** pill and scroll so the circuit, the slider "Oracle phase φ on door \|11⟩" and the switch "Diffuser (reflect about the average)" sit above the Run bar. Exactly **two** Run simulation clicks, so the IonQ run is run 3 of par 3 and earns all three stars.

| Line | Phrase | Action |
|---|---|---|
| s08b | "The prize is behind door one-one" | Pointer on the slider label, then rest it on the thumb at 0° |
| | "I mark it with a phase" | Drag to **180° (π)**, then move straight down to **Run simulation** |
| | "On its own" | Click **Run simulation** (Diffuser off) |
| | "the mark is invisible: twenty-five percent each" | Headline "The mark is invisible."; four bars near 25% |
| | "The diffuser" | Click the **Diffuser** switch on |
| | "about the average" | Click **Run simulation** |
| | "One query: one hundred percent" | "Found it with one query! You solved the level."; \|11⟩ at 100% |
| | "Four arrows line up on the prize" | Scroll fast past the histogram until the **second row** of arrow cards is visible; \|11⟩ is the bottom-right card with the cyan border. Keep rolling 2 s |
| s09a | (in the pause) | Scroll up so the results headline, the feedback card and the Run bar are on screen |
| | "Now, Confirm on IonQ" | Click **Confirm on IonQ** |
| | "as one job" | Status "Running 1000 shots on …" (a seconds counter may tick) |
| | (after s09a) | **Stop the audio, keep recording** until the IonQ result arrives. Then play s09b |
| s09b | "then confirm once" | The violet button reads "IonQ job used" and is greyed out |
| | "IonQ agrees: three stars" | Three stars: "Target met", "Solved in 3 runs (par 3)", "Confirmed on IonQ's simulator" |
| tail | (no voice) | Scroll down to "This circuit as Qiskit code" (bottom of the left panel, below "Need a hint?"), click it, hold 3 s on the code. Then click **All puzzles**, scroll to the five level rows, hold 3 s |

If the IonQ job fails or comes back under 90%: press Stop, then Run (IonQ simulator), click **Continue level 5**, scroll to **Reset puzzle** under the Run bar and press it, then redo s08b and s09.

### `07_keyboard.mp4` and `07c_inspect.mp4` (s10, second half; record these **right after take 05**, same Run)

* **Keyboard (about 4 s):** take 05 ends on the start page, so first get back to Amplifier: click the **Amplifier** row ("Play again") you just framed, or scroll up and click **Continue level 5**. Amplifier's last result comes back. Scroll until the slider "Oracle phase φ on door \|11⟩" is visible, then click the grey line "Rotates the arrow of the \|11⟩ door only. 180° flips its sign." (not the bold label), press Tab twice until the slider has the thick **yellow** focus outline, then start recording. Press Right (195°), Left (back to 180° (π)), Tab (the outline moves to "+").
* **Inspect (about 3 s, optional):** right-click the \|11⟩ arrow drawing, choose Inspect, then click the parent row `<svg viewBox="0 0 240 240" role="img" aria-label="Outcome |11⟩: 4 path arrows. …">`.

### `06_mobile.mp4` (s10, first half; about 3 s)

Now press **Stop**, then **Run** and choose the IonQ simulator again (progress is saved), so the phone bar reads "Run" and "IonQ". Open DevTools device mode (Ctrl+Shift+M), device **iPhone 12 Pro** (390×844). The game reopens on the start page. Scroll to "Five puzzles" and tap the **Invisible Ink** row ("Play again"). Recombine is still on and the dial still at 180° (π), both saved from take 02. Press **−** three times so the readout says **135° (3π/4)**, then scroll to the circuit. Record: scroll slowly down past the dial (the Run bar stays pinned to the bottom), then tap **Run**; "Last run: … goal ≥ 90%" and "View results" appear.

### `08_code.mp4` (s11; about 10.3 s of the 15.2 s on screen, the rest comes from the take 05 tail)

Dark editor theme, font 18 to 20 pt, sidebar hidden. Run `python -m pytest -q` just before recording.

| Phrase | Shot |
|---|---|
| "It's real Qiskit, MIT licensed" (about 2.5 s) | Take 05 tail: the "This circuit as Qiskit code" panel |
| "with two hundred and seven tests, and every level is checked for IonQ" (about 5 s, record 8 s) | `tests/test_api_and_execution.py` at lines 164 and 165 (`@pytest.mark.parametrize("level", LEVELS, …)`, `def test_circuits_serialize_for_ionq_offline(level):`) with the terminal's last line "207 passed in …" |
| "To add a puzzle, write one Level in levels dot py and one feedback function" (about 5.3 s, record 7 s) | Split editor: `phaseshift/levels.py` line 318 `KICKBACK = Level(` on the left, `phaseshift/game.py` line 152 `def _kickback(…)` on the right |
| "The interface builds itself" (about 2.4 s) | Take 05 tail: the five level rows (frame the generated rows, not the "Five puzzles" heading) |

## Voiceover (exact text)

The voice reads numbers as words; the captions show digits. Times are in the full track.

**s01 · 0:00.8 · Hook** (Clip 1)
> Phase Shift is a puzzle game about interference: what makes a quantum computer more than a coin flip.

**s02 · 0:07.2 · Runs on Qollab**
> It runs on Qollab: press Run, choose IonQ's simulator, and Qiskit starts in your browser.

**s03a · 0:14.8 · The only rule**
> Here's the only rule you need.

**s03b · 0:17.0 · Arrows** (Clip 2)
> Every path carries an arrow. Where paths meet, the arrows add head to tail.

**s03c · 0:23.0 · Lined up or opposite**
> Lined up, a detector lights up. Opposite, they cancel: it goes dark.

**s04 · 0:28.5 · Level 1**
> Level 1, Invisible Ink. A Hadamard splits the qubit into two paths; a phase turns the lower path's arrow. I run it at 0°: 50/50. I turn it to 180° and run again: still 50/50. The phase is invisible: measuring sees an arrow's length, not its direction.

**s05 · 0:49.0 · Recombine**
> I switch on a second Hadamard so the paths meet. Same phase, run: 100%. Why? Follow the arrows. Classical rules give 50%; quantum rules give 100%. That difference is interference, and no coin flip can reach it.

**s06 · 1:08.4 · Levels 2 and 3**
> Dark Port hides a phase: brightness tells you how far you are from dark. In the Eraser, a spying detector kills the interference. Erase what it knows, and interference returns, but only in the correlations.

**s07a · 1:22.6 · New: Kickback** (Clip 3)
> New: level 4, Kickback.

**s07b · 1:25.7 · Kickback demo**
> A controlled phase acts only when both qubits are 1. With the target at 0, the phase vanishes. Flip the target with an X, and the phase kicks back onto the control: it reads 1, while the target stays 1. That's the trick behind phase estimation and Shor's algorithm.

**s08a · 1:43.8 · New: Amplifier** (Clip 4)
> Also new: level 5, Amplifier, a 2-qubit Grover search.

**s08b · 1:49.8 · Amplifier demo**
> The prize is behind door 11. I mark it with a phase. On its own, the mark is invisible: 25% each. The diffuser reflects every arrow about the average. One query: 100%. Four arrows line up on the prize.

**s09a · 2:06.4 · Confirm on IonQ**
> Now, Confirm on IonQ. This exact circuit goes to IonQ's simulator as one job.

**s09b · 2:13.3 · One job per Run**
> Qollab allows one IonQ job per Run, so you practise in the browser, then confirm once. IonQ agrees: three stars.

**s10 · 2:23.2 · Phone and accessibility**
> On a phone, Run stays under your thumb. It's keyboard and screen-reader accessible: the histogram is a table, and every arrow is described in text.

**s11 · 2:32.5 · Open source**
> It's real Qiskit, MIT licensed, with 207 tests, and every level is checked for IonQ. To add a puzzle, write one Level in levels.py and one feedback function. The interface builds itself.

**s12 · 2:47.7 · Outro** (outro still)
> Phase Shift. Five puzzles, one rule: follow the arrows. Play it on Qollab.

## Editing plan

* **Title (s01):** "Phase Shift" large and white, with the kicker "A quantum interference puzzle · Qollab × IonQ" in cyan, in the empty lower half of Clip 1; fade in at about 1 s.
* **Labels** (top right, two lines, cyan kicker plus white title): "RUNS ON QOLLAB / IonQ simulator" (s02, s03), "LEVEL 1 / Invisible Ink" (s04, s05), "LEVELS 2 AND 3 / Dark Port, Which-Path Eraser" (s06), "NEW / Level 4: Kickback" (s07), "NEW / Level 5: Amplifier (Grover)" (s08), "IONQ VIA QOLLAB / one job per Run" (s09), "ACCESSIBLE / phone, keyboard, screen reader" (s10), "OPEN SOURCE / MIT · Qiskit · 207 tests" (s11). Optional footnote in s09: "compiled with optimization_level=0: IonQ's gate set, never simplified".
* **Zooms** (eased, at most 1.7×): the start-page detector cards (s03c), the feedback text (s04), the Recombine switch and then the \|1⟩ arrow card (s05), "Your phase vanished" and the per-qubit table (s07b), the \|11⟩ arrow card (s08b), the IonQ status line and the "IonQ job used" button (s09), the histogram table (s10), "207 passed" (s11).
* **Cut marks:** the Python and Qiskit load (after s02) and the IonQ wait (between s09a and s09b).
* **Captions:** import `captions_v2.srt`; it is already timed to the full track.
* **End card (s12):** over the outro still: "Phase Shift", "Five puzzles, one rule: follow the arrows.", the Qollab project link, the GitHub link, "MIT licensed · This effort is supported by Qollab & IonQ".
* **Audio:** the voice track is already at −16 LUFS; no music needed.
* **Privacy:** blur the Qollab account corner wherever it is visible.

`tools/demo_video/render.py` can do the cuts, zooms, labels, end card and blur boxes from an edit decision list, but not yet with this cut's timing: it puts 0.35 s before and 0.45 s after every line (`VO_LEAD`, `VO_TAIL`), which would space the 17 lines 0.8 s apart (3:00.0), and it writes its own captions. Any video editor works instead: lay the full voice track on the timeline, cut the recordings to the start times above and import `captions_v2.srt`. Send the recordings and `tools/demo_video/edl_v2.json` can be written with cut points, zoom boxes and blur boxes measured on the real footage, with `render.py` reading the lead and tail from it and run with `--no-captions`.

## Higgsfield assets

### What was made for this cut

| Asset | How | Higgsfield ids |
|---|---|---|
| Voice, 17 lines | `seed_audio`, preset voice Julian (`95429266-c0ac-4137-a209-63b8812b0f23`), WAV 48 kHz. s03c cut to 3.80 to 8.95 s of take `bb0bbca9` (`ffmpeg -i bb0bbca9.wav -af "atrim=3.80:8.95,asetpts=PTS-STARTPTS" raw/s03c.wav`), then all lines cleaned with `vo_clean.py raw clean 0.55 0.42`, joined with `assemble.py script_v2.json clean phase_shift_vo_v2.wav 0.4 0.8 2.0` and captioned with `make_captions.py script_v2.json clean captions_v2.srt 0.4 0.8` | job ids in [`assets/higgsfield_manifest.json`](../assets/higgsfield_manifest.json) |
| Clip 1 hook | Kling 3.0 `std`, 10 s, start and end keyframes; needle repainted with `clips/fix_hook.py` (Kling's needle wandered) and upscaled to 1080p | job `42b7921c-7491-4e1f-86ed-2a7a7d3ba77f` |
| Clip 2 arrows | Drawn exactly with `clips/arrows_anim.py` (Kling job `6c224785-745f-4321-8a8c-f084a86ab273` drew the white sum arrow wrong, so it was not used) | no generation |
| Clip 3 Kickback | Kling 3.0 `std`, 5 s, start and end keyframes, upscaled to 1080p | job `1c7fba75-b1df-4962-80f0-8e1671200efd` |
| Clip 4 Amplifier | Kling 3.0 `std`, 5 s, start and end keyframes, upscaled to 1080p | job `110364ea-6191-4c8e-b5c7-dba68a24a0f9` |

Keyframes are drawn from the game's own art by `tools/demo_video/clips/make_frames.py` (SVG, rendered to PNG with `render_svg.mjs`), so the clips match the game exactly. The clips from the first cut (`title_card`, `arrows_explainer`) still work as spare B-roll, but they are 1280×720 and show generic ripples, not the game.

### Specifications to make or remake a clip

* **Model:** Kling 3.0 (`kling3_0`), `mode: "std"` (1280×720; `"pro"` needs the Higgsfield Plus plan, this account is on Starter), `sound: "off"`, `aspect_ratio: "16:9"`, `duration` 3 to 15 s.
* **Keyframes:** `medias: [{value: <start PNG media id>, role: "start_image"}, {value: <end PNG media id>, role: "end_image"}]`. Both keyframes fix the composition, so the model only animates between them.
* **Prompt rules:** say "static locked-off camera", "flat 2D vector motion graphics", name every object by colour and position, say what must **not** move, and end with "No text, no new objects, no camera movement".
* **If a preset is suggested** instead of running, resend with its `declined_preset_id`.
* **After download:** `ffmpeg -i in.mp4 -vf "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p out_1080.mp4`.
* **Cost** (Starter, October 2026): Kling `std` 1.5 credits per second; voice 0.2 to 1.9 credits per line depending on its length (about 1 on average). This cut used about 59 credits: 39 for the four Kling clips (including the unused arrows try) and about 20 for 21 voice takes.

### Prompts used

**Clip 1 hook** (10 s; keyframes `hook_start.png` dial at 90°, both detectors half lit; `hook_end.png` dial at 180°, lower detector lit)
> Static locked-off camera, no zoom, no pan. Flat 2D vector motion graphics: an interferometer drawn in glowing lines on a dark navy background. A soft glow flows from the left along the white beam, then along the solid blue upper path and the dashed amber lower path at the same time, and the two merge at the right node. The white needle inside the small amber dial turns slowly a quarter turn counter-clockwise, from pointing up to pointing left, then stays still. As it turns, the upper right detector fades smoothly to dark while the lower right detector brightens into a strong white-cyan glow with a soft halo. Calm and elegant. The lower half of the frame stays empty dark navy. No text, no new objects, no particles, no 3D.

**Clip 2 arrows** (6 s; tried on Kling, replaced by the exact animation)
> Static locked-off camera. Flat 2D vector motion graphics on dark navy, two dotted circles side by side. In each circle a blue arrow points right from the centre and a dashed orange arrow starts at its tip. In the left circle the orange arrow swings smoothly down until it lines up with the blue arrow, and the white sum arrow from the centre grows long. In the right circle the orange arrow swings smoothly back until it points the opposite way, and the white sum arrow shrinks into a small white ring at the centre. Smooth and calm. No text, no new objects, no camera movement.

**Clip 3 Kickback** (5 s)
> Static locked-off camera. Flat 2D vector motion graphics on dark navy: a diamond made of a solid blue upper path and a dashed amber lower path between two white nodes, and a straight white target wire below it, joined to the diamond by a short cyan link. The white target wire stays perfectly steady at constant brightness the whole time; nothing travels along it. The faint curved cyan arrow beside the link lights up and glows brightly, the dashed amber lower path brightens, and the right white node blooms with a soft cyan halo. Calm and smooth. No text, no new objects, no camera movement.

**Clip 4 Amplifier** (5 s)
> Static locked-off camera. Flat 2D vector motion graphics on dark navy: four equal blue bars stand on a thin baseline under a dashed amber line, with a small amber diamond marker above the fourth bar. All four bars change at the same moment, simultaneously, with no sweep and no left-to-right motion: the first three bars sink smoothly down to the baseline while the fourth bar rises tall and turns glowing cyan, and the marker rises with it. The dashed amber line stays in place. Calm and smooth. No text, no new objects, no camera movement.

**Voice lines:** `generate_audio` with `model: "seed_audio"`, `voice_type: "preset"`, `voice_id: "95429266-c0ac-4137-a209-63b8812b0f23"`, `format: "wav"`, `sample_rate: 48000`, and the `tts` text of one line from `script_v2.json` (or `text` when there is no `tts`). Send at most three at a time (bursts are rate-limited) and check each file with Whisper: one take of s03c silently dropped its first sentence.

## Recording your own voice instead

Read the voiceover above into a USB or phone microphone in a quiet room. Make one WAV per line, named by the id in its heading (17 files): `s01.wav`, `s02.wav`, `s03a.wav`, `s03b.wav`, `s03c.wav`, `s04.wav`, `s05.wav`, `s06.wav`, `s07a.wav`, `s07b.wav`, `s08a.wav`, `s08b.wav`, `s09a.wav`, `s09b.wav`, `s10.wav`, `s11.wav`, `s12.wav`. Put them in `tools/demo_video/raw/`, then run these from `tools/demo_video/`:

```bash
python3 vo_clean.py raw/ clean/ 0.55 0.42
python3 assemble.py script_v2.json clean/ my_vo.wav 0.4 0.8 2.0       # prints the new timing sheet
python3 make_captions.py script_v2.json clean/ my_captions.srt 0.4 0.8  # needs ffmpeg and faster-whisper
```

The shot list works the same way; only the times shift. Cut to the start times in the sheet that `assemble.py` prints, and import `my_captions.srt` instead of `captions_v2.srt`, which is timed to the Julian voice only.

## Publishing (must be viewable without signing in)

1. Upload to **YouTube**: *Create → Upload video*. Title: "Phase Shift: a quantum interference puzzle (Qollab × IonQ Hackathon 2026)".
2. Description: a two-line summary, the Qollab project link, the GitHub link, "MIT licensed", and "This effort is supported by Qollab & IonQ."
3. Audience: "No, it's not made for kids". Visibility: **Unlisted** (anyone with the link can watch, no sign-in) or **Public**. Do **not** choose Private.
4. Open the link in a private window to confirm it plays without signing in.
5. Paste the link into the Qollab project page ("Demo video"), the README (top) and the hackathon submission form.
