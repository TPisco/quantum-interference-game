# Developer guide

## Big picture

```
main.js ──static import──▶ phaseshift.api ──▶ levels · circuits · paths · execution · game
   │                            ▲
   └─ web/bridge.js ── fn.callPromising(backend, ...args) ── returns a PyProxy → toJs() → plain object
```

The Python package does all the quantum work and the game rules, and returns plain dictionaries. The page only draws and handles input. The same `main.js` runs on Qollab (Pyodide) and locally (the `dev/` shim that forwards to CPython).

## Python modules (`phaseshift/`)

| Module | Main contents |
|---|---|
| `levels.py` | `Control` (angle slider or on/off toggle), `Step` (one gate: `h` on every listed qubit, `x`, `p`, `cp`, `cx`, `mystery`, `diffuser`), `Target` (summed outcome probability vs threshold), `Level` (all of it plus story, hints, par, and an optional `marginal_note` that turns on the per-qubit table). `LEVELS` (five puzzles), `get_level(id)`, `mystery_phase(seed)` (Dark Port's hidden θ, deterministic per seed). |
| `circuits.py` | `normalize_config(level, config)` validates player input and snaps angles to the 15° grid. `build_circuit(level, config, seed=, measure=, hide_mystery=)` returns the `QuantumCircuit`. `diffuser_gate()` is Grover's two-qubit diffuser as one labelled gate (so the path sum shows four arrows per door). `qiskit_code()` returns the readable Qiskit source shown in the UI. `circuit_text()` returns the ASCII drawing (hidden phase shown as "θ ?"). `angle_text(135)` → `"135° (3π/4)"`. |
| `paths.py` | `enumerate_paths(qc)`: every computational-basis path and its amplitude. `analyze(qc)`: per outcome, the arrows, the sum, classical Σ\|a\|², quantum \|Σa\|² and the interference term, checked against `Statevector`. `marginal(probs, qubit, n)`. |
| `execution.py` | `local_backend()` (BasicSimulator), `aer_backend()`, `ionq_backend(noise_model=, token=)` (qiskit-ionq, `IONQ_API_KEY`), `get_backend(kind)`. `is_ionq()`, `backend_name()`. `compile_for(backend, qc)` (IonQ gate set or the backend's target, `optimization_level=0`, idle qubits dropped). `submit()` / `run_circuit()` (one circuit per job). `normalize_counts()`, `to_probabilities()`, `wilson_interval()`. |
| `game.py` | `evaluate(level, config, probabilities, runs=, on_ionq=, seed=)` → `Feedback` (solved, value, stars, headline, detail, tone). Level-specific feedback writers in `_WRITERS`. Progress: `new_progress()`, `clean_progress()`, `record()`, `unlocked()`, `next_level()`. |
| `api.py` | JS-facing functions, all returning `{"ok": True, ...}` or `{"ok": False, "error", "code"}` and never raising: `info()`, `backend_info(backend)`, `default_config(level)`, `progress_status(progress)`, `preview(level, config, seed)`, `run_level(backend, level, config, options)`. Holds the one-IonQ-job-per-backend-object guard. |
| `__main__.py` | Command-line runner: `python -m phaseshift [--backend {local,aer,ionq}] [--level ... --phi ... --on ...]`. |

### `run_level` options and result

```python
api.run_level(backend, "invisible-ink", {"phi": 180, "recombine": True},
              {"where": "local" | "backend", "shots": 1000, "seed": 123,
               "runs_before": 0, "progress": {...}})
```

Result keys: `config`, `source` (`where`, `name`, `is_ionq`, `seconds`), `shots`, `counts`, `probabilities` (for example `{"0": 0.002, "1": 0.998}`), `outcomes` (label, count, measured, ci, is_target, plus theory/classical/interference/arrows/sum when `revealed`), `marginals` (2-qubit levels), `target` (+ `value`), `feedback`, `learn`, `runs`, `progress`, `unlocked`, `next_level`, `circuit_text`, `qiskit_code`.

Error codes: `bad_input`, `no_backend`, `ionq_job_used`, `backend_error`.

## Front-end modules

| File | Role |
|---|---|
| `index.html` | Body-only markup (Qollab inserts it into its page). Two views in one document: `#ps-view-start` (start page) and `#ps-view-play` (puzzle workspace). All ids start with `ps-`. |
| `main.css` | Styles, all scoped under `.ps`. Colour tokens at the top. |
| `main.js` | Boot, view switching and focus management, puzzle list and stepper, controls, runs, results. **Keep** the static `import * as api from "phaseshift.api"` and the final `await new Promise(() => {})`. |
| `web/bridge.js` | Calls into Python: positional `callPromising`, `toJs` + `destroy`, busy flag, 180 s timeout, paint before blocking. |
| `web/render.js` | Circuit SVG (with a compact layout for narrow screens), phase clock, histogram table, goal meter, marginals, arrow diagrams, all with text alternatives. |
| `web/demo.js` | The start page's live one-qubit interferometer (plain JS, exact formulas, one intro sweep). |
| `web/icons.js` | A few Phosphor icons (MIT) as path data, plus `hydrateIcons()` for the `data-icon` placeholders in `index.html`. |
| `web/store.js` | localStorage persistence (wrapped in try/catch). |
| `web/art.js`, `web/art-data.js` | Generated art as data URIs, with SVG emblem fallbacks (one per puzzle). |

## Add a level (step by step)

Levels 4 (Kickback) and 5 (Amplifier) were added exactly this way. Example: a "Balanced Paths" level where the player gets two phase gates, one on each path, and must learn that only their difference matters.

1. **Describe it** in `phaseshift/levels.py`:

   ```python
   BALANCE = Level(
       id="balance", number=6, title="Balanced Paths",
       concept="Only phase differences matter",
       tagline="Two dials, one outcome.",
       story="...", num_qubits=1, qubit_names=("qubit",),
       steps=(
           Step("h", (0,), "Split (H)", short="Split"),
           Step("p", (0,), "Lower phase P(α)", angle="alpha", short="Lower"),
           Step("x", (0,), "Swap paths (X)", short="Swap"),      # x, cp, diffuser already exist
           Step("p", (0,), "Upper phase P(β)", angle="beta", short="Upper"),
           Step("x", (0,), "Swap back (X)", short="Swap"),
           Step("h", (0,), "Recombine (H)", short="Recombine"),
       ),
       controls=(Control("alpha", "angle", "Phase α (lower path)", "...", 0.0),
                 Control("beta", "angle", "Phase β (upper path)", "...", 90.0)),
       target=Target(("1",), ">=", 0.9, "Measure |1⟩ at least 90% of the time.", "P(|1⟩) ≥ 90%"),
       hints=("...", "...", "..."), learn="...", par_runs=3,
   )
   LEVELS = (INVISIBLE_INK, DARK_PORT, ERASER, KICKBACK, AMPLIFIER, BALANCE)
   ```

2. **New gate types** (only if needed): handle them in `circuits.build_circuit` and `circuits._code_lines`, and draw them in `web/render.js` (`circuitSVG`, `stepName`). Every gate in `execution.IONQ_BASIS` or one that translates to it works on IonQ; `test_circuits_serialize_for_ionq_offline` checks it.
3. **Feedback**: write `_balance(level, cfg, value, solved, phi, seed)` in `phaseshift/game.py` returning `(headline, detail, tone)`, and register it in `_WRITERS`. Keep the house style: say what happened, then one concrete thing to try.
4. **Art**: add an emblem to `EMBLEMS` and alt text to `LEVEL_ALT` in `web/art.js` (the puzzle list shows it), or a Higgsfield prompt to `assets/higgsfield_manifest.json` and run `tools/embed_art.py`.
   If the per-qubit table teaches something in your level, set `marginal_note`.
5. **Tests**: add the level's formula to `tests/test_physics.py`. The generic tests (solvable on the dial, default not solved, path sum = statevector, IonQ serialization, the shown Qiskit code builds the same unitary) pick the level up automatically. Add the solution to `SOLUTIONS` in `phaseshift/__main__.py`.
6. Run `pytest`, then `python dev/server.py` and play it.

The UI needs no other change: the puzzle list, stepper, controls, circuit diagram, histogram and arrows are generated from `api.info()` and the run result.

## Other extension ideas

* **Noise as a teacher:** run the same circuit on IonQ's ideal simulator and with `noise_model="aria-1"`; show how noise shrinks the interference term (the arrows get shorter).
* **Deutsch's algorithm level:** one oracle query; kickback plus interference tells constant from balanced (it reuses Kickback's mechanism).
* **Too much Grover:** give the Amplifier a second iteration toggle; on two qubits a second round sends P(|11⟩) from 100% back down to 25%.
* **Animated arrows:** interpolate φ and redraw `arrowSVG` to show arrows swinging into or out of line.
* **Fringe plot:** after a level is solved, sweep the dial on the local simulator and plot measured vs theory (the notebook already does this).

## Interface conventions

* **Tokens** live at the top of `main.css` under `.ps`: colours (one UI accent, cyan; blue, amber and violet are data colours), radii (16 / 12 / 8 px), and the easing curves `--ease-out` and `--ease-in-out`.
* **Breakpoints:** 640, 768 and 1024 px. One column below 1024 px; the circuit switches to its compact drawing when its box is narrower than 520 px (`COMPACT_BELOW` in `main.js`, watched with a `ResizeObserver`).
* **Motion:** animate `transform` and `opacity` only, under 300 ms, with `--ease-out`. Pressables scale to 0.97 on `:active`; hover styles sit inside `@media (hover: hover) and (pointer: fine)`; entrances use `@starting-style`. View switches started from the keyboard are instant (`data-instant`). `prefers-reduced-motion` keeps fades only.
* **Accessibility:** every new control needs a visible label, a 44 px target and a text alternative for anything drawn. Screen-reader-only text uses `.ps-sr`; inside a scrolling container, give the nearest item `position: relative` so the hidden text cannot widen the page.
* **z-index:** 1 for the sticky Run bar, 10 for the skip link. Nothing else.

## Platform notes (Qollab)

* Only **static** imports of Python modules are resolved: `import * as api from "phaseshift.api"`.
* `backend` is created by Qollab from *Select QPU*. Pass it **positionally** as the first argument.
* An IonQ job accepts **one circuit**, and each Run allows **one IonQ job**. Jobs only reach IonQ while `main.js` top-level code is still pending, hence the final `await new Promise(() => {})`.
* Python runs on the browser's main thread: keep local simulations small (they take milliseconds here) and let the page paint before calling (`bridge.nextPaint()`).
* Data files must be referenced by literal paths in Python to be preloaded. This project avoids data files altogether and embeds art in JS modules.
* Upload limits: at most 100 files, each under 2 MB; README under 65,000 characters. `tools/package_qollab.py` checks them.

These rules were found by other teams on the platform during the hackathon (and partly confirmed by Qollab mentors). Re-check them on Qollab if anything behaves differently.
