/*
  Phase Shift - page orchestrator (identical on Qollab and in local development).

  - `import * as api from "phaseshift.api"` must stay STATIC: it is the form
    Qollab resolves to the Python module phaseshift/api.py (run by Pyodide).
    Locally, dev/index.html maps the name to dev/py-shim.js instead.
  - Two views in one document: the start page (level list, live demo, rules)
    and the puzzle workspace. Switching never touches the URL.
  - Practice runs go to an in-browser Qiskit simulator (where: "local").
    "Confirm on IonQ" sends one job to the backend chosen in Qollab's
    "Select QPU" dialog (where: "backend"). Qollab allows one IonQ job per Run.
  - The LAST line keeps top-level code pending: Qollab only lets jobs reach
    IonQ while main.js is still running (its Stop button still ends the run).
*/

import * as api from "phaseshift.api";
import { createBridge } from "./web/bridge.js";
import { loadState, saveState, newSeed } from "./web/store.js";
import { levelArt } from "./web/art.js";
import { icon, hydrateIcons } from "./web/icons.js";
import { mountDemo } from "./web/demo.js";
import {
  el, angleText, pct, circuitSVG, histogramTable, goalMeter,
  marginalsTable, arrowCard, arrowKey, arrowReach, phaseClock, interferenceCurve,
} from "./web/render.js";

const $ = (id) => document.getElementById(id);
const els = {
  app: $("ps-app"),
  back: $("ps-back"),
  backend: $("ps-backend"),
  viewStart: $("ps-view-start"),
  viewPlay: $("ps-view-play"),
  startTitle: $("ps-start-title"),
  start: $("ps-start"),
  startLabel: $("ps-start-label"),
  howtoBtn: $("ps-howto-btn"),
  rules: $("ps-rules"),
  demo: $("ps-demo"),
  levelList: $("ps-level-list"),
  stepper: $("ps-stepper"),
  levelArt: $("ps-level-art"),
  levelNum: $("ps-level-num"),
  levelTitle: $("ps-level-title"),
  levelConcept: $("ps-level-concept"),
  levelStory: $("ps-level-story"),
  goalText: $("ps-goal-text"),
  circuit: $("ps-circuit"),
  controls: $("ps-controls"),
  curve: $("ps-curve"),
  curveBadge: $("ps-curve-badge"),
  curveBody: $("ps-curve-body"),
  runLast: $("ps-run-last"),
  runLastText: $("ps-run-last-text"),
  runLastJump: $("ps-run-last-jump"),
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
  hintLabel: $("ps-hint-label"),
  hintList: $("ps-hint-list"),
  status: $("ps-status"),
  empty: $("ps-empty"),
  feedback: $("ps-feedback"),
  fbStars: $("ps-feedback-stars"),
  fbHeadline: $("ps-feedback-headline"),
  fbDetail: $("ps-feedback-detail"),
  fbReasons: $("ps-feedback-reasons"),
  next: $("ps-next"),
  nextLabel: $("ps-next-label"),
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

const reduceMotion = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
const bridge = createBridge(api);
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
  const navButtons = [...els.levelList.querySelectorAll("button"), ...els.stepper.querySelectorAll("button")];
  for (const b of [els.runLocal, els.reset, ...navButtons]) {
    b.disabled = busy || (b.dataset.locked === "true");
  }
  for (const input of els.controls.querySelectorAll("input, button")) input.disabled = busy;
  els.runBackend.disabled = busy || !backendUsable();
  els.feedback.parentElement.setAttribute("aria-busy", String(busy));
}

function backendUsable() {
  return backendState.available && !(backendState.is_ionq && backendState.ionq_job_used);
}

function starsEl(n, size = 16) {
  const s = Math.max(0, Math.min(3, Number(n) || 0));
  const wrap = el("span", { class: "ps-stars" });
  for (let i = 0; i < 3; i++) wrap.append(icon(i < s ? "starFill" : "star", size, i < s ? "" : "ps-star-off"));
  wrap.append(el("span", { class: "ps-sr", text: `${s} of 3 stars` }));
  return wrap;
}

// ------------------------------------------------------------------- views

function showView(view, { focus = true, instant = false } = {}) {
  const play = view === "play";
  els.app.dataset.view = view;
  for (const [name, node] of [["start", els.viewStart], ["play", els.viewPlay]]) {
    // Keyboard-initiated switches appear instantly; pointer ones get a short fade.
    if (instant || reduceMotion) node.setAttribute("data-instant", "");
    else node.removeAttribute("data-instant");
    node.hidden = name !== view;
  }
  els.back.hidden = !play;
  if (play) renderCircuit();
  if (els.app.getBoundingClientRect().top < 0) els.app.scrollIntoView({ block: "start" });
  if (!focus) return;
  if (play) {
    els.levelTitle.focus({ preventScroll: true });
  } else {
    const row = level && els.levelList.querySelector(`[data-level="${level.id}"]:not([disabled])`);
    (row ?? els.startTitle).focus({ preventScroll: true });
  }
}

function continueTarget() {
  if (unlocked.includes(state.current)) return state.current;
  const unsolved = ORDER.find((id) => unlocked.includes(id) && !(state.progress.stars?.[id] > 0));
  return unsolved ?? ORDER[0];
}

function renderStartCta() {
  const id = continueTarget();
  const l = LEVELS[id];
  const fresh = !Object.keys(state.progress.stars ?? {}).length && !state.attempts[id]?.runs;
  els.startLabel.textContent = fresh ? `Start level ${l.number}` : `Continue level ${l.number}`;
  els.start.dataset.target = id;
}

// ---------------------------------------------------------------- backend UI

function renderBackend() {
  const b = backendState;
  const short = (lead, tail) => [el("span", { class: "ps-hide-sm", text: lead }), tail];
  if (!b.available) {
    els.backend.textContent = "Practice mode: no quantum backend selected";
    els.runBackendLabel.replaceChildren(...short("Confirm on ", "IonQ"));
    els.backendNote.textContent = "To confirm a solution on IonQ, press Run on Qollab and choose IonQ's simulator in “Select QPU”. Practice runs work without it.";
  } else if (b.is_ionq) {
    els.backend.textContent = `Backend: ${b.name} (IonQ)`;
    if (b.ionq_job_used) {
      els.runBackendLabel.replaceChildren(...short("IonQ ", "job used"));
      els.backendNote.textContent = "Qollab allows one IonQ job per Run. Press Stop, then Run, to send another. Your circuit and progress are saved in this browser.";
    } else {
      els.runBackendLabel.replaceChildren(...short("Confirm on ", "IonQ"));
      els.backendNote.textContent = `Sends this exact circuit to ${b.name} as one job. It takes a few seconds, and Qollab allows one IonQ job per Run, so practise first.`;
    }
  } else {
    els.backend.textContent = `Backend: ${b.name}`;
    els.runBackendLabel.replaceChildren(...short("Run on ", "QPU"));
    els.backendNote.textContent = `Runs on ${b.name}, the backend selected in Qollab. Choose IonQ's simulator in “Select QPU” to earn the IonQ star.`;
  }
  els.runBackend.disabled = bridge.busy || !backendUsable();
}

// ------------------------------------------------------------------ levels

function renderLevelRows() {
  els.levelList.removeAttribute("aria-busy");
  els.levelList.replaceChildren(...ORDER.map((id) => {
    const l = LEVELS[id];
    const open = unlocked.includes(id);
    const stars = state.progress.stars?.[id] ?? 0;
    const ionq = (state.progress.ionq ?? []).includes(id);
    const btn = el("button", {
      type: "button", class: "ps-level-row", "data-level": id, "data-locked": String(!open), disabled: !open,
    },
    el("span", { class: "ps-level-row__art" }, levelArt(id, { decorative: true, size: 64 })),
    el("span", {},
      el("span", { class: "ps-level-row__num", text: `Level ${l.number}` }),
      el("span", { class: "ps-level-row__title", text: l.title }),
      el("span", { class: "ps-level-row__concept", text: open ? l.concept : `Solve level ${l.number - 1} to unlock` })),
    el("span", { class: "ps-level-row__side" },
      el("span", {}, starsEl(stars), ionq ? el("span", { class: "ps-ionq-tag", text: " IonQ" }) : null),
      el("span", { class: "ps-level-row__go" },
        open ? [stars ? "Play again" : "Play", icon("arrowRight", 16)] : [icon("lock", 16), "Locked"])));
    btn.addEventListener("click", (e) => {
      selectLevel(id);
      showView("play", { instant: e.detail === 0 });
    });
    return el("li", {}, btn);
  }));
}

function renderStepper() {
  els.stepper.replaceChildren(...ORDER.map((id) => {
    const l = LEVELS[id];
    const open = unlocked.includes(id);
    const stars = state.progress.stars?.[id] ?? 0;
    const btn = el("button", {
      type: "button", class: "ps-lvl-pill", "data-level": id, "data-locked": String(!open), disabled: !open,
      "aria-current": level?.id === id ? "step" : null,
    },
    el("span", { class: "ps-lvl-pill__num", "aria-hidden": "true" }, open ? String(l.number) : icon("lock", 14)),
    el("span", { class: "ps-sr", text: `Level ${l.number}: ` }),
    el("span", { text: l.title }),
    open ? (stars ? starsEl(stars, 12) : null) : el("span", { class: "ps-sr", text: ", locked" }));
    btn.addEventListener("click", () => selectLevel(id, { focus: true }));
    return el("li", {}, btn);
  }));
  // Keep the current pill in view horizontally (never scroll the page vertically).
  const cur = els.stepper.querySelector('[aria-current="step"]');
  if (cur && els.stepper.scrollWidth > els.stepper.clientWidth) {
    const box = els.stepper.getBoundingClientRect();
    const r = cur.getBoundingClientRect();
    els.stepper.scrollLeft += r.left - box.left - (box.width - r.width) / 2;
  }
}

function renderNav() {
  renderLevelRows();
  renderStepper();
  renderStartCta();
}

function renderControls() {
  const a = attempt();
  els.controls.replaceChildren();
  for (const c of level.controls) {
    const id = `ps-ctl-${c.id}`;
    if (c.kind === "angle") {
      const input = el("input", {
        type: "range", id, class: "ps-range", min: c.min, max: c.max, step: c.step, value: a.config[c.id],
        "aria-describedby": `${id}-desc`, "aria-valuetext": angleText(a.config[c.id]),
      });
      const out = el("output", { for: id, id: `${id}-out`, class: "ps-readout__value" });
      const clock = el("span", { class: "ps-readout__clock" });
      const show = (val) => {
        input.value = String(Math.min(val, c.max));
        input.setAttribute("aria-valuetext", angleText(val));
        input.style.setProperty("--fill", `${(100 * Math.min(val, c.max)) / c.max}%`);
        out.textContent = angleText(val);
        clock.replaceChildren(phaseClock(val));
      };
      const set = (v) => {
        const val = ((Math.round(v / c.step) * c.step) % 360 + 360) % 360;
        a.config[c.id] = val;
        show(val);
        onConfigChange();
      };
      show(a.config[c.id]);
      input.addEventListener("input", () => set(Number(input.value)));
      const minus = el("button", { type: "button", class: "ps-step", "aria-label": `Decrease ${c.label} by ${c.step}°`, text: "−" });
      const plus = el("button", { type: "button", class: "ps-step", "aria-label": `Increase ${c.label} by ${c.step}°`, text: "+" });
      minus.addEventListener("click", () => set(a.config[c.id] - c.step));
      plus.addEventListener("click", () => set(a.config[c.id] + c.step));
      els.controls.append(el("div", { class: "ps-control" },
        el("div", { class: "ps-control__head" },
          el("label", { class: "ps-control__label", for: id, text: c.label }),
          el("span", { class: "ps-readout" }, clock, out)),
        el("span", { class: "ps-control__desc", id: `${id}-desc`, text: c.description }),
        el("div", { class: "ps-dial" }, minus, input, plus)));
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
  previewTimer = setTimeout(() => {
    renderCode();
    renderCurve();
  }, 120);
}

const COMPACT_BELOW = 520;
function renderCircuit() {
  if (!level) return;
  const w = els.circuit.clientWidth;
  const compact = w > 0 && w < COMPACT_BELOW;
  els.circuit.dataset.compact = String(compact);
  els.circuit.replaceChildren(circuitSVG(level, attempt().config, { compact }));
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

// The interference curve is a reward: it unlocks once a level is solved, so it
// never gives a puzzle away (Dark Port's hidden phase in particular).
function curveUnlocked() {
  return (state.progress.stars?.[level.id] ?? 0) > 0;
}

let curveRequest = 0;
async function renderCurve() {
  if (!level) return;
  const open = curveUnlocked();
  els.curve.dataset.locked = String(!open);
  els.curveBadge.textContent = open ? "" : "· unlocks when you solve this puzzle";
  if (!open) {
    els.curveBody.replaceChildren(el("p", { class: "ps-hidden-note", text:
      "Solve this puzzle first. Then this panel draws the goal value for every phase φ, so you can see exactly why your answer works and how each gate reshapes the interference." }));
    return;
  }
  if (!els.curve.open || bridge.busy) return;
  const ticket = ++curveRequest;
  const a = attempt();
  const sw = await bridge.sweep(level.id, a.config, a.seed, true);
  if (ticket !== curveRequest || !sw?.ok || sw.level !== level.id) return;
  if (sw.hidden) return;
  els.curveBody.replaceChildren(interferenceCurve(sw));
}

function renderRunsUsed() {
  const a = attempt();
  els.runsUsed.textContent = `Runs: ${a.runs} (par ${level.par_runs})`;
}

function resetHints() {
  hintsShown = 0;
  els.hintList.replaceChildren();
  els.hintBtn.disabled = false;
  els.hintLabel.textContent = "Need a hint?";
}

function showHint() {
  if (hintsShown >= level.hints.length) return;
  els.hintList.append(el("li", { text: level.hints[hintsShown] }));
  hintsShown += 1;
  if (hintsShown >= level.hints.length) {
    els.hintLabel.textContent = "No more hints";
    els.hintBtn.disabled = true;
  } else {
    els.hintLabel.textContent = `Another hint (${hintsShown + 1} of ${level.hints.length})`;
  }
}

function clearResults() {
  els.empty.hidden = false;
  els.feedback.hidden = true;
  els.goalmeter.hidden = true;
  els.histogram.replaceChildren();
  els.marginals.replaceChildren();
  els.arrowsWrap.hidden = true;
  els.arrowKey.replaceChildren();
  els.arrows.replaceChildren();
  els.learn.hidden = true;
  els.runLast.hidden = true;
  setStatus("Ready. Change the circuit, then press Run.");
}

function selectLevel(id, { focus = false } = {}) {
  if (!unlocked.includes(id) || bridge.busy) return;
  level = LEVELS[id];
  attempt();
  save();
  els.levelArt.replaceChildren(levelArt(id, { size: 88 }));
  els.levelNum.textContent = `Level ${level.number} of ${ORDER.length}`;
  els.levelTitle.textContent = level.title;
  els.levelConcept.textContent = level.concept;
  els.levelStory.textContent = level.story;
  els.goalText.textContent = level.target.description;
  renderNav();
  renderControls();
  renderCircuit();
  renderCode();
  renderCurve();
  renderRunsUsed();
  resetHints();
  if (lastResults[id]) renderResult(lastResults[id], { announce: false });
  else clearResults();
  if (focus) els.levelTitle.focus();
}

// ------------------------------------------------------------------ results

function renderResult(res, { announce = true } = {}) {
  const fb = res.feedback;
  els.empty.hidden = true;
  els.feedback.hidden = false;
  els.feedback.dataset.tone = fb.tone;
  els.fbStars.replaceChildren(...(fb.solved ? [starsEl(fb.stars, 22)] : []));
  els.fbHeadline.textContent = fb.headline;
  els.fbDetail.textContent = fb.detail;
  els.fbReasons.replaceChildren(...(fb.star_reasons ?? []).map((r) => el("li", {}, icon("starFill", 14), r)));
  if (fb.solved && !res.source.is_ionq && backendState.is_ionq && !backendState.ionq_job_used) {
    els.fbReasons.append(el("li", {}, icon("star", 14), "Confirm this circuit on IonQ to earn the IonQ star."));
  }
  const nextOpen = fb.solved && res.next_level && unlocked.includes(res.next_level);
  const finished = fb.solved && !res.next_level;
  els.next.hidden = !(nextOpen || finished);
  els.next.dataset.target = nextOpen ? res.next_level : finished ? "__start__" : "";
  els.nextLabel.textContent = nextOpen ? `Next: ${LEVELS[res.next_level].title}` : "All puzzles";

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

  // "P(|1⟩) ≥ 90%" -> measure "P(|1⟩)", goal "≥ 90%".
  const [measure, goal = ""] = res.target.short.split(/ (?=[≥≤])/);
  els.runLast.hidden = false;
  els.runLast.dataset.met = String(fb.solved);
  els.runLastText.textContent = `Last run: ${measure} = ${pct(res.target.value, 1)}, ${fb.solved ? "goal met" : `goal ${goal}`}`;

  if (announce) {
    const where = res.source.is_ionq ? `on IonQ (${res.source.name})` : `on ${res.source.name}`;
    setStatus(`Done ${where} in ${res.source.seconds} s. ${fb.headline} ${measure} = ${pct(res.target.value, 1)}.`,
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
  renderCode(); // a preview skipped while busy would otherwise stay stale
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
  renderNav();
  renderRunsUsed();
  renderCurve(); // solving unlocks it
  if (level.id === runLevelId) renderResult(res);
}

async function resetLevel() {
  if (bridge.busy) return;
  state.attempts[level.id] = { config: { ...level.default_config }, seed: newSeed(), runs: 0 };
  delete lastResults[level.id];
  save();
  selectLevel(level.id);
  setStatus(`Puzzle reset: gates back to the start${level.has_mystery ? ", and a new mystery phase" : ""}. Run counter at 0.`);
}

// --------------------------------------------------------------------- boot

async function boot() {
  hydrateIcons(els.app);
  const demo = mountDemo(els.demo, { reduceMotion });

  const info = await bridge.info();
  if (!info?.ok) throw new Error(info?.error ?? "Python module did not load");
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

  els.start.addEventListener("click", (e) => {
    selectLevel(els.start.dataset.target || ORDER[0]);
    showView("play", { instant: e.detail === 0 });
  });
  els.howtoBtn.addEventListener("click", () => {
    els.rules.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    els.rules.focus({ preventScroll: true });
  });
  els.back.addEventListener("click", (e) => showView("start", { instant: e.detail === 0 }));
  els.runLocal.addEventListener("click", () => run("local"));
  els.runBackend.addEventListener("click", () => run("backend"));
  els.runLastJump.addEventListener("click", () => {
    els.feedback.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    els.feedback.focus({ preventScroll: true });
  });
  els.reset.addEventListener("click", resetLevel);
  els.hintBtn.addEventListener("click", showHint);
  els.curve.addEventListener("toggle", () => {
    if (els.curve.open) renderCurve();
  });
  els.controls.addEventListener("submit", (e) => e.preventDefault());
  els.next.addEventListener("click", (e) => {
    const id = els.next.dataset.target;
    if (id === "__start__") showView("start", { instant: e.detail === 0 });
    else if (id) selectLevel(id, { focus: true });
  });

  // Re-draw the circuit when its box crosses the compact-layout width.
  if (typeof ResizeObserver === "function") {
    let wasCompact = null;
    new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      const compact = w > 0 && w < COMPACT_BELOW;
      if (compact !== wasCompact) {
        wasCompact = compact;
        renderCircuit();
      }
    }).observe(els.circuit);
  }

  selectLevel(continueTarget());
  renderNav();
  els.start.disabled = false;
  demo.play();
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
