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

**Quantum Unlocked (secondary).** It teaches three ideas that usually stay abstract:

1. A phase is real but invisible to a measurement on its own.
2. Recombining paths turns a phase into a measurable brightness (constructive or destructive interference). This is how interferometers and quantum sensors read phase.
3. Which-path information destroys interference, and erasing it restores the interference, which then lives in the correlations (quantum eraser).

**Beyond the tutorial bar.** The original educational contribution is the **"Follow the arrows"** panel: after each run, the game enumerates every computational-basis path through the player's own circuit (an exact Feynman path sum, `phaseshift/paths.py`). It draws each path's amplitude as an arrow and shows, per outcome:

* classical probability = Σ|arrow|²
* quantum probability = |Σ arrow|²
* interference term = quantum − classical

The same rule explains all three levels with one picture: one arrow per outcome means no interference; two arrows means interference. On top of that come two game mechanics with real quantum content: **phase estimation from measured brightness** (Dark Port, with a hidden phase and a par of 2 runs) and **interference hidden in correlations** (the eraser level shows the photon's own marginal staying at 50/50).

**Technical execution on IonQ.** Each solution can be confirmed as one single-circuit job on IonQ's simulator through Qollab, which respects the platform's one-job-per-Run rule. Results are shown with 95% Wilson intervals, so shot noise is visible and honest.

## Learning objectives

After playing, a player can:

1. **Superposition (H):** explain that a Hadamard sends |0⟩ into two paths at once, and that measuring right away gives 50/50.
2. **Phase (P(φ), RZ):** explain why changing φ alone never changes the measured counts: it rotates an arrow without changing its length.
3. **Interference:** predict that H·P(φ)·H gives P(|1⟩) = sin²(φ/2), and use φ = 180° to turn certain |0⟩ into certain |1⟩.
4. **Phase sensing:** infer an unknown phase from a measured brightness, and resolve the ± ambiguity with a second measurement.
5. **Which-path information:** explain why entangling the path with a detector removes interference, and why the eraser restores it only in the joint (correlated) outcomes.

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

## Scoring and progression

* ★ target met · ★ within par runs · ★ confirmed on IonQ's simulator (the "IonQ seal").
* Level 1 is open; solving level N unlocks level N + 1. Best stars are kept.
* **Reset level** restores the starting gates, sets the run counter to 0 and, in Dark Port, draws a new mystery phase.
* Progress, circuit settings and the Dark Port seed are saved in the browser, so a Qollab Stop → Run (needed for another IonQ job) does not lose anything.

## Why a hackathon team can ship this in 48 hours

Three one- or two-qubit circuits, a pure-Python simulator for practice runs, one IonQ job per confirmation, and a single-page UI without a framework or build step. The path-sum explainer is about 60 lines of Python.
