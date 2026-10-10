# Phase Shift: game design

## Title options

| Title | Why it works |
|---|---|
| **Phase Shift** (chosen) | Names the one thing you control (the phase) and what it does to the outcome. Short, memorable. |
| Interfere! | Says the core verb out loud; playful. |
| Bright & Dark | Describes what players see: outcomes that light up or go dark. |
| Arrows of Chance | Points to the amplitude-arrow visualisation that explains every result. |
| Qubit Lightworks | Interferometer and optics flavour. |

## One-sentence pitch

> **Phase Shift is a quantum interference puzzle: you steer an invisible phase until a qubit's two paths meet and add up, or cancel out, to hit a target measurement probability, live on IonQ's simulator.**

## Theme alignment

**Quantum Playground (primary).** It is a game, and the quantum effect is the game mechanic rather than a dice roller. Every puzzle is solved by making amplitudes interfere. A classical random-number generator cannot solve any level, because every level's target is out of reach of "flip a fair coin": each classical path combination gives 50/50 (or 25% each), and only interference gets to 0% or 100%. The UI shows this side by side for every outcome: *classical* (add probabilities) against *quantum* (add arrows, then square).

**Quantum Unlocked (secondary).** It teaches five ideas that usually stay abstract:

1. A phase is real but invisible to a measurement on its own.
2. Recombining paths turns a phase into a measurable brightness (constructive or destructive interference). This is how interferometers and quantum sensors read phase.
3. Which-path information destroys interference, and erasing it restores the interference, which then lives in the correlations (quantum eraser).
4. A controlled phase has no owner: when the target is in |1⟩, the phase lands on the control (phase kickback, the read-out mechanism of Deutsch-Jozsa, phase estimation and Shor).
5. Interference can be steered to concentrate probability on one answer (Grover's amplitude amplification).

**Beyond the tutorial bar.** The original educational contribution is the **"Follow the arrows"** panel: after each run, the game enumerates every computational-basis path through the player's own circuit (an exact Feynman path sum, `phaseshift/paths.py`). It draws each path's amplitude as an arrow and shows, per outcome:

* classical probability = Σ|arrow|²
* quantum probability = |Σ arrow|²
* interference term = quantum − classical

The same rule explains all five puzzles with one picture: one arrow per outcome means no interference; several arrows means interference. In the Amplifier, four arrows land on every door and line up only on the prize. On top of that come two game mechanics with real quantum content: **phase estimation from measured brightness** (Dark Port, with a hidden phase and a par of 2 runs) and **interference hidden in correlations** (the eraser level shows the photon's own marginal staying at 50/50).

**Technical execution on IonQ.** Each solution can be confirmed as one single-circuit job on IonQ's simulator through Qollab, which respects the platform's one-job-per-Run rule. Results are shown with 95% Wilson intervals, so shot noise is visible and honest.

## Learning objectives

After playing, a player can:

1. **Superposition (H):** explain that a Hadamard sends |0⟩ into two paths at once, and that measuring right away gives 50/50.
2. **Phase (P(φ), RZ):** explain why changing φ alone never changes the measured counts: it rotates an arrow without changing its length.
3. **Interference:** predict that H·P(φ)·H gives P(|1⟩) = sin²(φ/2), and use φ = 180° to turn certain |0⟩ into certain |1⟩.
4. **Phase sensing:** infer an unknown phase from a measured brightness, and resolve the ± ambiguity with a second measurement.
5. **Which-path information:** explain why entangling the path with a detector removes interference, and why the eraser restores it only in the joint (correlated) outcomes.
6. **Phase kickback:** explain why CP(φ) does nothing to a target in |0⟩, and why with the target in |1⟩ the phase shows up on the control while the target stays unchanged.
7. **Amplitude amplification:** use a phase oracle plus the diffuser (2 × average − amplitude) to find a marked item among four with one query, and predict P(|11⟩) = (10 − 6 cos φ)/16.

## Levels

All angles are in degrees; the phase dial moves in 15° steps (24 positions). Outcome keys use Qiskit's order (rightmost bit = qubit 0).

### Level 1: Invisible Ink (superposition and phase)

| | |
|---|---|
| Story | H splits the qubit into an upper path |0⟩ and a lower path |1⟩. Paint a phase on the lower path. Can a measurement see it? |
| Qubits | 1 |
| Circuit | `H` (fixed) → `P(φ)` (player) → `H` (player toggle "Recombine", off at start) → measure |
| Player actions | Phase dial φ ∈ {0°, 15°, …, 345°}; Recombine on/off |
| Target | P(|1⟩) ≥ 90% |
| Physics | Recombine off: P(|1⟩) = 1/2 for every φ. Recombine on: P(|1⟩) = sin²(φ/2), solved at φ = 180° (165° and 195° give 98.3% and also pass) |
| Hints | (1) Run with the recombiner off at two phases: does the histogram change? (2) Measurement sees arrow lengths, not directions; switch on the second H. (3) With both H on, P(|1⟩) = sin²(φ/2). |
| Feedback | Recombiner off → "The phase is invisible!"; on and ≥ 50% → "You're close. Try adjusting the phase gate to change interference."; on and < 50% → "favours |0⟩, rotate further"; solved → "You solved the level! Here's what your circuit did." with a step-by-step explanation |
| Par | 4 runs |

### Level 2: Dark Port (destructive interference as a phase detector)

| | |
|---|---|
| Story | A mystery sample adds an unknown phase θ to the lower path of a ready-made interferometer. Cancel it so detector |1⟩ goes dark. |
| Qubits | 1 |
| Circuit | `H` → `P(θ)` (hidden; θ from the attempt seed, a multiple of 15°, never 0° or 180°) → `P(φ)` (player) → `H` → measure |
| Player actions | Phase dial φ |
| Target | P(|1⟩) ≤ 5% |
| Physics | P(|1⟩) = sin²((θ + φ)/2): dark when φ ≡ −θ (± 15° still passes at 1.7%) |
| Hints | (1) Start at φ = 0 and run once. (2) P(|1⟩) = sin²(Δ/2) with Δ = θ + φ; 50% means Δ = ±90°. (3) Brightness gives the size, not the sign; turn one way, and if it gets brighter go the other way. |
| Feedback | Not solved → the measured brightness is turned into an estimate "Δ ≈ ±X°"; ≤ 20% → "You're close…"; solved → reveals θ and explains the cancellation |
| Fairness | The arrows panel and exact theory are hidden until solved (they would reveal θ). The drawing shows the hidden gate as "θ ?". |
| Par | 2 runs (one to measure the distance, one to resolve the sign) |

### Level 3: Which-Path Eraser (entanglement and the quantum eraser)

| | |
|---|---|
| Story | A CNOT copies "which path?" into a detector qubit; the interference disappears. You cannot remove the detector, but you can choose how to read it. |
| Qubits | 2 (q0 = photon, q1 = detector) |
| Circuit | `H(q0)` → `CNOT(q0→q1)` (fixed detector) → `P(φ)` on q0 (player) → `H(q0)` → `H(q1)` (player toggle "Eraser", off at start) → measure both |
| Player actions | Phase dial φ; Eraser on/off |
| Target | P(photon ≠ detector) = P(01) + P(10) ≥ 90% |
| Physics | Eraser off: all four outcomes 25%, "disagree" = 50% for every φ. Eraser on: P(disagree) = sin²(φ/2). The photon on its own stays at 50/50 in every case |
| Hints | (1) With the eraser off, try two phases. (2) Paths that can be told apart cannot interfere; switch the eraser on. (3) With the eraser on, P(disagree) = sin²(φ/2); look at the photon alone too. |
| Feedback | Eraser off → "The detector knows which path the photon took."; close → "You're close…"; solved → explains the eraser and that the pattern lives in the correlation |
| Par | 4 runs |

### Level 4: Kickback (phase kickback)

| | |
|---|---|
| Story | Two qubits. The control goes through split and recombine as in level 1, but the phase gate is a controlled phase CP(φ): it adds φ only when control AND target are both 1. The target starts in |0⟩; an X can flip it. |
| Qubits | 2 (q0 = control, q1 = target) |
| Circuit | `H(q0)` → `X(q1)` (player toggle "Flip", off at start) → `CP(φ)(q0, q1)` (player) → `H(q0)` → measure both |
| Player actions | Phase dial φ; Flip on/off |
| Target | P(control = 1) = P(01) + P(11) ≥ 90% |
| Physics | Flip off: CP does nothing (no |11⟩ component) and H·H = I, so the control reads 0 every time. Flip on: CP(φ) acts as P(φ) on the control, so P(control = 1) = sin²(φ/2); the target reads 1 every time |
| Hints | (1) Set 180° with the flip off: did the control notice? (2) CP only acts where both qubits are 1; flip the target. (3) With the target in |1⟩, P(control = 1) = sin²(φ/2). |
| Feedback | Flip off → "Your phase vanished."; flip on and φ = 0 → "no phase to kick"; ≥ 50% → "You're close."; solved → "Kicked back!" with the explanation that the target never changed |
| Par | 3 runs |

The per-qubit table is shown here because it carries the lesson: the target's own P(1) stays at 100%.

### Level 5: Amplifier (Grover search on two qubits)

| | |
|---|---|
| Story | Four doors, |00⟩ to |11⟩, the prize behind |11⟩. Two H gates open all four at once. An oracle marks the prize with a phase φ; a diffuser reflects every amplitude about the average. Find the prize with one query. |
| Qubits | 2 |
| Circuit | `H` on both → `CP(φ)` (player, the oracle: phase on |11⟩ only) → `Diffuser` (player toggle, off at start; one gate = H H, Z Z, CZ, H H = 2\|s⟩⟨s\| − I) → measure both |
| Player actions | Oracle phase φ; Diffuser on/off |
| Target | P(|11⟩) ≥ 90% |
| Physics | Diffuser off: 25% each for every φ (one arrow per door). Diffuser on: P(|11⟩) = (10 − 6 cos φ)/16, 25% at φ = 0 and 100% at φ = 180° (150° to 210° pass). At 180° the amplitudes before the diffuser are (+½, +½, +½, −½) with average ¼, so the empty doors go to 0 and the prize to 1 |
| Hints | (1) Turn the oracle with the diffuser off: do the doors change? (2) The oracle only rotates one arrow; switch on the diffuser so four paths meet on every door. (3) P(|11⟩) = (10 − 6 cos φ)/16. |
| Feedback | Diffuser off → "The mark is invisible."; on and φ = 0 → "Nothing to amplify yet."; ≥ 50% → "You're close."; solved → "Found it with one query!" |
| Par | 3 runs |

The diffuser is drawn and simulated as one two-qubit gate so the arrows panel shows four arrows per door (all aligned on |11⟩, cancelling in pairs elsewhere) instead of sixteen. Transpilation unrolls it for every backend, including IonQ.

## Interface

**Start page (persuade).** The first screen states the promise in one sentence ("Five quantum puzzles about interference…"), offers one primary action (**Start level 1**, or **Continue level N** once you have progress) and shows a working one-qubit interferometer instead of a decorative picture: turning its phase dial swings the two amplitude arrows into line (detector |1⟩ lights up) or against each other (it goes dark). On first view the dial sweeps once from 0° to 180° to show this, then stops for good. Below: the five puzzles as a list with stars, IonQ badges and locks, and the four rules (Split, Rotate, Measure, Interfere) with the star system.

**Puzzle workspace (operate).** A level stepper replaces the old level cards; the build panel keeps story, goal, circuit and controls together, and the Run bar sticks to the bottom of the screen with the last result, so the player can iterate without scrolling back and forth. Results sit beside the controls from 1024 px wide and below them on phones.

**Design rules.** One dark theme; cyan is the only UI accent, while blue, amber and violet stay data colours (upper path, lower path and phase, hidden phase and IonQ). Radii: panels 16 px, controls 12 px, chips round. Motion uses transform and opacity only, ease-out curves and durations under 300 ms; nothing animates on keyboard-initiated view changes; reduced motion keeps fades only.

## Scoring and progression

* ★ target met · ★ within par runs · ★ confirmed on IonQ's simulator (the "IonQ seal").
* Level 1 is open; solving level N unlocks level N + 1. Best stars are kept.
* **Reset level** restores the starting gates, sets the run counter to 0 and, in Dark Port, draws a new mystery phase.
* Progress, circuit settings and the Dark Port seed are saved in the browser, so a Qollab Stop → Run (needed for another IonQ job) does not lose anything.

## Why a hackathon team can ship this in 48 hours

Five one- or two-qubit circuits, a pure-Python simulator for practice runs, one IonQ job per confirmation, and a single-page UI without a framework or build step. The path-sum explainer is about 60 lines of Python, and each new puzzle is one `Level` definition plus one feedback function.
