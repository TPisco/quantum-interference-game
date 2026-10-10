# Qollab project page: text to paste

Copy each section into the matching field of the Qollab project page. Replace the two links at the end.

---

## Title

**Phase Shift: a quantum interference puzzle**

## Short description (2–3 sentences)

Phase Shift is a puzzle game where you steer invisible quantum phases until a qubit's paths meet and add up, or cancel out, to hit a target measurement probability. Five puzzles take you from "a phase alone does nothing you can see" to measuring a hidden phase, erasing which-path information, phase kickback and Grover search, and every result is explained with Feynman-style amplitude arrows built from your own circuit. Practise instantly in the browser, then confirm your solution as a real Qiskit job on IonQ's simulator.

## What it does

The start page opens with a live one-qubit interferometer: turn its phase dial and watch two amplitude arrows line up (a detector lights up) or cancel (it goes dark). Each puzzle is then a small Qiskit circuit with some gates you control: a phase gate P(φ), a second Hadamard that recombines the paths, an "eraser" Hadamard on a detector qubit, an X, a controlled phase, Grover's diffuser. You run it, read a histogram with honest error bars, and try to reach the target:

1. **Invisible Ink** (superposition and phase): make the qubit read |1⟩ at least 90% of the time using only H and phase gates. The twist: with the paths left apart, the phase changes nothing. Every φ gives 50/50. Recombining the paths with a second H turns the phase into a probability: P(|1⟩) = sin²(φ/2).
2. **Dark Port** (destructive interference as a sensor): a mystery sample adds a hidden phase θ. Dial a compensating phase so detector |1⟩ goes dark (≤ 5%). The brightness you measure tells you how far you are; a second run tells you which way. Par is two runs, the same trick interferometers use to measure tiny phase shifts.
3. **Which-Path Eraser** (entanglement and the quantum eraser): a CNOT copies "which path?" into a detector qubit and the interference vanishes. Erase the record by measuring the detector in another basis, and the interference comes back. It only shows in the correlations, though: the photon on its own stays at 50/50.
4. **Kickback** (phase kickback): your phase gate is now a controlled phase on a second qubit, and fires only when both qubits are 1. With the target in |0⟩ the phase vanishes; flip the target with an X and the phase lands on the control, while the target never changes. This is how Deutsch-Jozsa, phase estimation and Shor's algorithm read out an oracle.
5. **Amplifier** (Grover search): four doors, the prize behind |11⟩. Marking it with a phase changes nothing on its own (25% each); add the diffuser, which reflects every amplitude about the average, and one oracle query finds the prize: P(|11⟩) = (10 − 6 cos φ)/16, 100% at φ = 180°.

Stars reward solving, solving within par, and confirming the solution on IonQ's simulator. Solving a level unlocks the next.

## Problem it explores / theme

**Quantum Playground**, with a strong **Quantum Unlocked** angle. Most "quantum games" use measurement as a dice roll. Here, randomness alone cannot win: every target is out of reach for a classical coin model (always 50/50 or 25% each), and only interference gets you to 0% or 100%. The game makes this explicit. For every outcome it shows the **classical** prediction (add the probabilities of the paths), the **quantum** result (add the amplitude arrows, then square) and their difference, the **interference term**.

The educational contribution is the **"Follow the arrows"** view. After each run, the game enumerates every path through *your* circuit (an exact path sum computed from the gate matrices) and draws each path's amplitude as an arrow. One rule explains all five puzzles: *if only one arrow reaches an outcome, phases are invisible; if several arrows reach it, they interfere.* The same rule explains why a which-path detector kills interference (it gives each path a different destination), why the eraser revives it (both paths share destinations again), and why Grover's diffuser works (four arrows reach every door; only on the marked one do they line up).

## Technical approach

* **Qiskit circuits.** `phaseshift/levels.py` describes each level as data (gates, player controls, target). `phaseshift/circuits.py` builds a `QuantumCircuit` from the level and the player's settings: H, X, P(φ), CP(φ), CX, a two-qubit Grover diffuser and measurements, 1 or 2 qubits.
* **Execution.** Practice runs use Qiskit's `BasicSimulator` inside the browser (unlimited, instant). "Confirm on IonQ" sends the same circuit to the backend chosen in Qollab's *Select QPU* dialog as **one single-circuit job**. Circuits are translated to IonQ's gate set without re-optimisation (`optimization_level=0`; P → RZ, CP → RZ + CX), so IonQ runs exactly the circuit the player built. Qollab allows one IonQ job per Run; the game guards against a second submission and tells the player to press Stop and Run, while saving their progress.
* **Theory and statistics.** `phaseshift/paths.py` computes the exact path sum (checked against Qiskit's `Statevector` on every call). Measured probabilities come with 95% Wilson intervals, and the solve check uses the measured result.
* **Hybrid structure.** The page (HTML/CSS/JS, no framework, no build step) handles interaction and drawing: a start view and a puzzle workspace in one document, responsive from phone to desktop (sticky Run bar, compact circuit drawing on narrow screens). The Python package handles circuits, execution, physics and game rules, and returns plain dictionaries. The page calls Python with Qollab's Pyodide bridge (`import * as api from "phaseshift.api"`, then `api.run_level.callPromising(backend, level, config, options)`).
* **Accessibility.** Keyboard-operable controls, visible focus, high-contrast colours, text equivalents for every chart (the histogram is a data table; each arrow diagram has a full description), and no information carried by colour alone. Reduced-motion and forced-colours modes are respected. Checked with axe-core: 0 WCAG 2.1 AA violations.
* **Quality.** 207 automated tests cover the formulas for every level, path sums against the statevector, solvability on the 15° dial, the API, progression, and IonQ payload serialization (`qiskit_to_ionq`).

## How to run it

1. Open this project in **Chrome or Edge** and press **Run**.
2. In **Select QPU**, choose **IonQ's simulator** (Qollab's built-in simulator also works).
3. Wait a few seconds for Python and Qiskit to load. The top bar shows the selected backend, and the start page fills in.
4. Try the dial on the start page, then press **Start level 1** or pick an unlocked puzzle from the list (each solved puzzle unlocks the next; **All puzzles** brings you back).
5. **Change the circuit:** turn the phase dial (drag, arrow keys or the −/+ buttons) and switch gates on or off. The circuit diagram updates live; "This circuit as Qiskit code" shows the exact code.
6. **Run simulation** as often as you like (the Run bar stays at the bottom of the screen and shows the last result). Read the result:
   * **Goal meter**: your current value against the target.
   * **Histogram table**: measured share of each outcome, its 95% range, and the exact theory.
   * **Follow the arrows**: why the result came out that way (hidden in Dark Port until solved, because it would give the answer away).
   * **Feedback**: what happened and what to try next. **Need a hint?** reveals up to three hints.
7. **Confirm on IonQ:** sends your circuit to IonQ's simulator as one job and earns the IonQ star if it meets the target. To send another IonQ job, press **Stop**, then **Run**: your progress and settings are kept.
8. **Reset puzzle** restores the starting gates (and draws a new mystery phase in Dark Port).

Run it outside Qollab: `pip install -r requirements-dev.txt`, then `python dev/server.py` (web UI) or `python -m phaseshift` (command line). Set `IONQ_API_KEY` to use IonQ's cloud simulator through `qiskit-ionq`.

## How to extend it

* **New levels:** append a `Level` to `phaseshift/levels.py` (steps, controls, target, hints) and a feedback function in `phaseshift/game.py`. The UI builds the puzzle list, controls, circuit diagram and results from `api.info()`, so no front-end change is needed. Good candidates: a Mach-Zehnder with two phase gates (only the difference matters), a three-path interferometer, Deutsch's algorithm (one query decides constant vs balanced through kickback and interference), two Grover iterations (too many overshoot), or Bell-state correlations.
* **New gates:** add a gate type to `Step` and to `build_circuit` (for example RY or S/T), and a label in `web/render.js`.
* **Noise:** compare IonQ's ideal simulator with its `aria-1` / `forte-1` noise models (`execution.ionq_backend(noise_model=...)`) and show how noise shrinks the interference term.
* **Visualisations:** animate the arrows as φ changes, add a Bloch-sphere view, or plot the measured fringe across all dial positions.

The developer guide (`docs/DEVELOPER_GUIDE.md`) lists every module and function, and gives the steps above in detail.

## License, credits and links

* License: **MIT**.
* Built with Qiskit for the Qollab × IonQ Global Hackathon 2026. Video art and clips generated with Higgsfield; icons by Phosphor (MIT).
* This effort is supported by Qollab & IonQ.
* Source code: _add your GitHub link_
* Demo video (2–3 min, no sign-in needed): _add your YouTube link_
