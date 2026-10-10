/*
  Phase Shift - page orchestrator (identical on Qollab and in local development).

  - `import * as api from "phaseshift.api"` must stay STATIC: it is the form
    Qollab resolves to the Python module phaseshift/api.py (run by Pyodide).
    Locally, dev/index.html maps the name to dev/py-shim.js instead.
  - Practice runs go to an in-browser Qiskit simulator (where: "local").
    "Confirm on IonQ" sends one job to the backend chosen in Qollab's
    "Select QPU" dialog (where: "backend"). Qollab allows one IonQ job per Run.
  - The LAST line keeps top-level code pending: Qollab only lets jobs reach
    IonQ while main.js is still running (its Stop button still ends the run).
*/

import * as api from "phaseshift.api";
import { createBridge } from "./web/bridge.js";
import { loadState, saveState, newSeed } from "./web/store.js";
import { applyHero, levelArt } from "./web/art.js";
import {
  el, angleText, pct, starsText, circuitSVG, histogramTable, goalMeter,
  marginalsTable, arrowCard, arrowKey, arrowReach,
} from "./web/render.js";

const $ = (id) => document.getElementById(id);
const els = {
  hero: $("ps-hero"),
  backend: $("ps-backend"),
  levelList: $("ps-level-list"),
  levelArt: $("ps-level-art"),
  levelNum: $("ps-level-num"),
  levelTitle: $("ps-level-title"),
  levelConcept: $("ps-level-concept"),
  levelStory: $("ps-level-story"),
  goalText: $("ps-goal-text"),
  circuit: $("ps-circuit"),
  controls: $("ps-controls"),
  runLocal: $("ps-run-local"),
  runBackend: $("ps-run-backend"),
  runBackendLabel: $("ps-run-backend-label"),
  backendNote: $("ps-backend-note"),
  reset: $("ps-reset"),
  shots: $("ps-shots"),
  runsUsed: $("ps-runs-used"),
  code: $("ps-qiskit-code"),
  circuitText: $("ps-circuit-text"),
  hintBtn: $("ps-hint-btn"),
  hintList: $("ps-hint-list"),
  status: $("ps-status"),
  feedback: $("ps-feedback"),
  fbStars: $("ps-feedback-stars"),
  fbHeadline: $("ps-feedback-headline"),
  fbDetail: $("ps-feedback-detail"),
  fbReasons: $("ps-feedback-reasons"),
  next: $("ps-next"),
  goalmeter: $("ps-goalmeter"),
  histogram: $("ps-histogram"),
  marginals: $("ps-marginals"),
  arrowsWrap: $("ps-arrows-wrap"),
  arrows: $("ps-arrows"),
  arrowKey: $("ps-arrow-key"),
  learn: $("ps-learn"),
  learnText: $("ps-learn-text"),
  attribution: $("ps-attribution"),
};

const bridge = createBridge(api);
let INFO = null;
let LEVELS = {};
let ORDER = [];
let unlocked = [];
let level = null;
let backendState = { available: false, name: null, is_ionq: false, ionq_job_used: false };
let hintsShown = 0;
const lastResults = {};
const state = loadState();

// ------------------------------------------------------------------ helpers

function attempt() {
  const a = (state.attempts[level.id] ??= {});
  // Keep only controls this version of the level has (saved state may be older).
  const saved = a.config ?? {};
  a.config = Object.fromEntries(Object.entries(level.default_config)
    .map(([k, v]) => [k, k in saved ? saved[k] : v]));
  if (typeof a.seed !== "number") a.seed = newSeed();
  if (typeof a.runs !== "number") a.runs = 0;
  return a;
}

function save() {
  state.current = level?.id ?? state.current;
  saveState(state);
}

function setStatus(text, kind = "ready") {
  els.status.textContent = text;
  els.status.dataset.state = kind;
}

function setBusy(busy) {
  for (const b of [els.runLocal, els.reset, ...els.levelList.querySelectorAll("button")]) {
    b.disabled = busy || (b.dataset.locked === "true");
  }
  for (const input of els.controls.querySelectorAll("input, button")) input.disabled = busy;
  els.runBackend.disabled = busy || !backendUsable();
  els.feedback.parentElement.setAttribute("aria-busy", String(busy));
}

function backendUsable() {
  return backendState.available && !(backendState.is_ionq && backendState.ionq_job_used);
}

// ---------------------------------------------------------------- backend UI

function renderBackend() {
  const b = backendState;
  if (!b.available) {
    els.backend.textContent = "Practice mode: no quantum backend selected";
    els.runBackendLabel.textContent = "Confirm on IonQ";
    els.backendNote.textContent = "To confirm a solution on IonQ, press Run on Qollab and choose IonQ's simulator in “Select QPU”. Practice runs work without it.";
  } else if (b.is_ionq) {
    els.backend.textContent = `Quantum backend: ${b.name} (IonQ)`;
    if (b.ionq_job_used) {
      els.runBackendLabel.textContent = "IonQ job used for this Run";
      els.backendNote.textContent = "Qollab allows one IonQ job per Run. Press Stop, then Run, to send another. Your circuit and progress are saved in this browser.";
    } else {
      els.runBackendLabel.textContent = "Confirm on IonQ (1 job per Run)";
      els.backendNote.textContent = `Sends this exact circuit to ${b.name} as one job. It takes a few seconds; Qollab allows one IonQ job per Run, so practise first.`;
    }
  } else {
    els.backend.textContent = `Quantum backend: ${b.name}`;
    els.runBackendLabel.textContent = `Run on ${b.name}`;
    els.backendNote.textContent = "Runs on the backend selected in Qollab. Choose IonQ's simulator in “Select QPU” to earn the IonQ star.";
  }
  els.runBackend.disabled = bridge.busy || !backendUsable();
}

// ------------------------------------------------------------------ levels

function renderLevelList() {
  els.levelList.replaceChildren();
  for (const id of ORDER) {
    const l = LEVELS[id];
    const open = unlocked.includes(id);
    const stars = state.progress.stars?.[id] ?? 0;
    const ionq = (state.progress.ionq ?? []).includes(id);
    const meta = open
      ? `${l.concept}`
      : `Locked: solve level ${l.number - 1} first`;
    const btn = el("button", {
      type: "button",
      class: "ps-level-btn",
      "aria-current": level?.id === id ? "step" : null,
      "data-locked": String(!open),
      disabled: !open,
    },
    el("span", { class: "ps-level-btn__num", "aria-hidden": "true", text: open ? String(l.number) : "🔒" }),
    el("span", {},
      el("span", { class: "ps-level-btn__title" }, `Level ${l.number}: ${l.title}`),
      el("span", { class: "ps-level-btn__meta" }, meta),
      el("span", { class: "ps-level-btn__meta" },
        el("span", { class: "ps-stars", "aria-hidden": "true", text: starsText(stars) }),
        el("span", { class: "ps-sr", text: `${stars} of 3 stars` }),
        ionq ? " · IonQ confirmed" : "")));
    btn.addEventListener("click", () => selectLevel(id, { focus: true }));
    els.levelList.append(el("li", {}, btn));
  }
}

function renderControls() {
  const a = attempt();
  els.controls.replaceChildren();
  for (const c of level.controls) {
    const id = `ps-ctl-${c.id}`;
    if (c.kind === "angle") {
      const input = el("input", {
        type: "range", id, min: c.min, max: c.max, step: c.step, value: a.config[c.id],
        "aria-describedby": `${id}-desc`, "aria-valuetext": angleText(a.config[c.id]),
      });
      const out = el("output", { for: id, id: `${id}-out`, text: angleText(a.config[c.id]) });
      const set = (v) => {
        const val = ((Math.round(v / c.step) * c.step) % 360 + 360) % 360;
        a.config[c.id] = val;
        input.value = String(Math.min(val, c.max));
        input.setAttribute("aria-valuetext", angleText(val));
        out.textContent = angleText(val);
        onConfigChange();
      };
      input.addEventListener("input", () => set(Number(input.value)));
      const minus = el("button", { type: "button", class: "ps-step", "aria-label": `Decrease ${c.label} by ${c.step}°`, text: "−" });
      const plus = el("button", { type: "button", class: "ps-step", "aria-label": `Increase ${c.label} by ${c.step}°`, text: "+" });
      minus.addEventListener("click", () => set(a.config[c.id] - c.step));
      plus.addEventListener("click", () => set(a.config[c.id] + c.step));
      els.controls.append(el("div", { class: "ps-control" },
        el("label", { class: "ps-control__label", for: id, text: c.label }),
        el("span", { class: "ps-control__desc", id: `${id}-desc`, text: c.description }),
        el("div", { class: "ps-dial" }, minus, input, plus, out)));
    } else if (c.kind === "toggle") {
      const input = el("input", { type: "checkbox", role: "switch", id, "aria-describedby": `${id}-desc` });
      input.checked = Boolean(a.config[c.id]);
      const stateTxt = el("span", { class: "ps-switch__state", "aria-hidden": "true", text: input.checked ? "ON" : "OFF" });
      input.addEventListener("change", () => {
        a.config[c.id] = input.checked;
        stateTxt.textContent = input.checked ? "ON" : "OFF";
        onConfigChange();
      });
      els.controls.append(el("div", { class: "ps-control" },
        el("label", { class: "ps-switch", for: id }, input, el("span", { text: c.label }), stateTxt),
        el("span", { class: "ps-control__desc", id: `${id}-desc`, text: c.description })));
    }
  }
}

let previewTimer = null;
function onConfigChange() {
  save();
  renderCircuit();
  clearTimeout(previewTimer);
  previewTimer = setTimeout(renderCode, 120);
}

function renderCircuit() {
  els.circuit.replaceChildren(circuitSVG(level, attempt().config));
}

async function renderCode() {
  if (bridge.busy) return;
  const a = attempt();
  const p = await bridge.preview(level.id, a.config, a.seed);
  if (p?.ok) {
    els.code.textContent = p.qiskit_code;
    els.circuitText.textContent = p.circuit_text;
  }
}

function renderRunsUsed() {
  const a = attempt();
  els.runsUsed.textContent = `Runs this attempt: ${a.runs} (par ${level.par_runs})`;
}

function resetHints() {
  hintsShown = 0;
  els.hintList.replaceChildren();
  els.hintBtn.disabled = false;
  els.hintBtn.textContent = "Need a hint?";
}

function showHint() {
  if (hintsShown >= level.hints.length) return;
  els.hintList.append(el("li", { text: level.hints[hintsShown] }));
  hintsShown += 1;
  if (hintsShown >= level.hints.length) {
    els.hintBtn.textContent = "No more hints";
    els.hintBtn.disabled = true;
  } else {
    els.hintBtn.textContent = `Another hint (${hintsShown + 1} of ${level.hints.length})`;
  }
}

function clearResults() {
  els.feedback.hidden = true;
  els.goalmeter.hidden = true;
  els.histogram.replaceChildren();
  els.marginals.replaceChildren();
  els.arrowsWrap.hidden = true;
  els.arrowKey.replaceChildren();
  els.arrows.replaceChildren();
  els.learn.hidden = true;
  setStatus("Ready. Change the circuit, then press Run.");
}

function selectLevel(id, { focus = false } = {}) {
  if (!unlocked.includes(id) || bridge.busy) return;
  level = LEVELS[id];
  attempt();
  save();
  els.levelArt.replaceChildren(levelArt(id));
  els.levelNum.textContent = `Level ${level.number} of ${ORDER.length}`;
  els.levelTitle.textContent = level.title;
  els.levelConcept.textContent = level.concept;
  els.levelStory.textContent = level.story;
  els.goalText.textContent = level.target.description;
  renderLevelList();
  renderControls();
  renderCircuit();
  renderCode();
  renderRunsUsed();
  resetHints();
  if (lastResults[id]) renderResult(lastResults[id], { announce: false });
  else clearResults();
  if (focus) {
    els.levelTitle.setAttribute("tabindex", "-1");
    els.levelTitle.focus();
  }
}

// ------------------------------------------------------------------ results

function renderResult(res, { announce = true } = {}) {
  const fb = res.feedback;
  els.feedback.hidden = false;
  els.feedback.dataset.tone = fb.tone;
  els.fbStars.replaceChildren(
    el("span", { "aria-hidden": "true", text: fb.solved ? starsText(fb.stars) : "" }),
    el("span", { class: "ps-sr", text: fb.solved ? `${fb.stars} of 3 stars.` : "" }));
  els.fbHeadline.textContent = fb.headline;
  els.fbDetail.textContent = fb.detail;
  els.fbReasons.replaceChildren(...(fb.star_reasons ?? []).map((r) => el("li", { text: `★ ${r}` })));
  if (fb.solved && !res.source.is_ionq && backendState.is_ionq && !backendState.ionq_job_used) {
    els.fbReasons.append(el("li", { text: "☆ Confirm this circuit on IonQ to earn the IonQ star." }));
  }
  els.next.hidden = !(fb.solved && res.next_level && unlocked.includes(res.next_level));
  els.next.dataset.target = res.next_level ?? "";

  els.goalmeter.hidden = false;
  els.goalmeter.replaceChildren(goalMeter(res));
  els.histogram.replaceChildren(histogramTable(res));
  const marg = marginalsTable(res);
  els.marginals.replaceChildren(...(marg ? [marg] : []));

  els.arrowsWrap.hidden = false;
  if (res.revealed) {
    els.arrowKey.replaceChildren(arrowKey());
    const reach = arrowReach(res.outcomes);
    els.arrows.replaceChildren(...res.outcomes.map((o) => arrowCard(o, reach)));
  } else {
    els.arrowKey.replaceChildren();
    els.arrows.replaceChildren(el("p", { class: "ps-hidden-note", text:
      "The arrows would give away the mystery phase θ, so they stay hidden until you solve this level. Use the brightness of detector |1⟩ instead: it tells you how far you are from dark." }));
  }
  els.learn.hidden = !res.learn;
  els.learnText.textContent = res.learn ?? "";

  if (announce) {
    const where = res.source.is_ionq ? `on IonQ (${res.source.name})` : `on ${res.source.name}`;
    setStatus(`Done ${where} in ${res.source.seconds} s. ${fb.headline} ${res.target.short.split(" ")[0]} = ${pct(res.target.value, 1)}.`,
      fb.solved ? "success" : "ready");
  }
}

async function run(where) {
  if (bridge.busy) return;
  const a = attempt();
  const runLevelId = level.id;
  const shots = Number(els.shots.value) || 1000;
  const label = where === "local" ? "the in-browser Qiskit simulator" : backendState.name ?? "the selected backend";
  setStatus(`Running ${shots} shots on ${label}…`, "running");
  setBusy(true);
  const res = await bridge.runLevel(runLevelId, a.config, {
    where, shots, seed: a.seed, runs_before: a.runs, progress: state.progress,
  }, {
    onTick: (s) => setStatus(`Running ${shots} shots on ${label}… ${s} s`, "running"),
  });
  setBusy(false);
  if (!res) return;
  if (!res.ok) {
    if (res.code === "ionq_job_used") backendState.ionq_job_used = true;
    renderBackend();
    setStatus(`Could not run: ${res.error}`, "error");
    return;
  }
  if (res.source.is_ionq) backendState.ionq_job_used = true;
  a.runs = res.runs;
  state.progress = res.progress;
  unlocked = res.unlocked;
  lastResults[runLevelId] = res;
  save();
  renderBackend();
  renderLevelList();
  renderRunsUsed();
  if (level.id === runLevelId) renderResult(res);
}

async function resetLevel() {
  if (bridge.busy) return;
  state.attempts[level.id] = { config: { ...level.default_config }, seed: newSeed(), runs: 0 };
  delete lastResults[level.id];
  save();
  selectLevel(level.id);
  setStatus(`Level reset: gates back to the start${level.has_mystery ? ", and a new mystery phase" : ""}. Run counter at 0.`);
}

// --------------------------------------------------------------------- boot

async function boot() {
  applyHero(els.hero);
  const info = await bridge.info();
  if (!info?.ok) throw new Error(info?.error ?? "Python module did not load");
  INFO = info;
  if (info.attribution) els.attribution.textContent = info.attribution;
  for (const l of info.levels) LEVELS[l.id] = l;
  ORDER = info.levels.map((l) => l.id);

  const ps = await bridge.progressStatus(state.progress);
  if (ps?.ok) {
    state.progress = ps.progress;
    unlocked = ps.unlocked;
  } else {
    unlocked = [ORDER[0]];
  }
  const b = await bridge.backendInfo();
  if (b?.ok) backendState = b;
  renderBackend();

  els.runLocal.addEventListener("click", () => run("local"));
  els.runBackend.addEventListener("click", () => run("backend"));
  els.reset.addEventListener("click", resetLevel);
  els.hintBtn.addEventListener("click", showHint);
  els.controls.addEventListener("submit", (e) => e.preventDefault());
  els.next.addEventListener("click", () => {
    const id = els.next.dataset.target;
    if (id) selectLevel(id, { focus: true });
  });

  const start = unlocked.includes(state.current) ? state.current : unlocked[unlocked.length - 1] ?? ORDER[0];
  selectLevel(start);
}

try {
  await boot();
} catch (err) {
  console.error(err);
  setStatus(`Startup failed: ${err?.message ?? err}`, "error");
  els.backend.textContent = "Could not start the Python game engine.";
}

// Keep the Qollab run alive so button clicks can still reach IonQ. Must stay the LAST line.
await new Promise(() => {});
