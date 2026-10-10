/*
  Start-page demo: one qubit through H, P(φ), H, computed in plain JS so the
  core idea is on screen before any puzzle starts. It reuses the game's arrow
  drawing, and the numbers are exact: P(|1⟩) = sin²(φ/2).

  On first show the dial sweeps once from 0° to 180° (an explanatory motion:
  watch |0⟩ go dark while |1⟩ lights up). Any pointer or key input stops it,
  and it is skipped entirely under prefers-reduced-motion.
*/

import { el, arrowSVG, angleText, pct, phaseClock } from "./render.js";

const STEP = 15;
const MAX = 345;

function outcomes(phiDeg) {
  const r = (phiDeg * Math.PI) / 180;
  const lower = { re: Math.cos(r) / 2, im: Math.sin(r) / 2 };
  const make = (label, sign) => {
    const arrows = [
      { re: 0.5, im: 0, arm: "upper" },
      { re: sign * lower.re, im: sign * lower.im, arm: "lower" },
    ];
    const sum = { re: arrows[0].re + arrows[1].re, im: arrows[0].im + arrows[1].im };
    const theory = sum.re ** 2 + sum.im ** 2;
    return { label, arrows, sum, theory, classical: 0.5, interference: theory - 0.5 };
  };
  return [make("|0⟩", 1), make("|1⟩", -1)];
}

const snap = (v) => (((Math.round(v / STEP) * STEP) % 360) + 360) % 360;

export function mountDemo(root, { reduceMotion = false } = {}) {
  const id = "ps-demo-phi";
  const input = el("input", {
    type: "range", id, class: "ps-range", min: 0, max: MAX, step: STEP, value: 0,
    "aria-describedby": "ps-demo-help",
  });
  const out = el("output", { for: id, class: "ps-readout__value" });
  const clock = el("span", { class: "ps-readout__clock" });
  const minus = el("button", { type: "button", class: "ps-step", "aria-label": `Decrease the demo phase by ${STEP}°`, text: "−" });
  const plus = el("button", { type: "button", class: "ps-step", "aria-label": `Increase the demo phase by ${STEP}°`, text: "+" });

  const dets = ["|0⟩", "|1⟩"].map((label) => {
    const art = el("div", { class: "ps-demo__art" });
    const value = el("span", { class: "ps-demo__pct" });
    const fill = el("span", { class: "ps-demo__fill" });
    const fig = el("div", { class: "ps-demo__det" },
      el("p", { class: "ps-demo__label" }, el("span", { text: `Detector ${label}` }), value),
      el("span", { class: "ps-demo__bar", "aria-hidden": "true" }, fill),
      art);
    return { fig, art, value, fill };
  });

  root.replaceChildren(
    el("div", { class: "ps-control ps-control--demo" },
      el("div", { class: "ps-control__head" },
        el("label", { class: "ps-control__label", for: id, text: "Phase φ on the lower path" }),
        el("span", { class: "ps-readout" }, clock, out)),
      el("div", { class: "ps-dial" }, minus, input, plus)),
    el("div", { class: "ps-demo__dets" }, ...dets.map((d) => d.fig)),
  );

  let raf = null;
  function render(value, { exact = false } = {}) {
    const shown = exact ? value : snap(value);
    const rounded = snap(value);
    input.value = String(Math.min(rounded, MAX));
    input.setAttribute("aria-valuetext", angleText(rounded));
    input.style.setProperty("--fill", `${(100 * Math.min(rounded, MAX)) / MAX}%`);
    out.textContent = angleText(rounded);
    clock.replaceChildren(phaseClock(shown));
    outcomes(shown).forEach((o, i) => {
      const d = dets[i];
      d.art.replaceChildren(arrowSVG(o, 1));
      d.value.textContent = pct(o.theory);
      d.fill.style.transform = `scaleX(${o.theory.toFixed(4)})`;
    });
  }

  function stop() {
    if (raf !== null) {
      cancelAnimationFrame(raf);
      raf = null;
      render(Number(input.value));
    }
  }

  const set = (v) => {
    stop();
    render(snap(v));
  };
  input.addEventListener("input", () => set(Number(input.value)));
  minus.addEventListener("click", () => set(Number(input.value) - STEP));
  plus.addEventListener("click", () => set(Number(input.value) + STEP));
  root.addEventListener("pointerdown", stop);
  root.addEventListener("keydown", stop);

  render(0);
  let swept = false;

  return {
    /** Run the one-time intro sweep (0° to 180°). */
    play() {
      if (swept || raf !== null) return;
      swept = true;
      if (reduceMotion) {
        render(180);
        return;
      }
      const ms = 1800;
      let t0 = null;
      const frame = (t) => {
        t0 ??= t;
        const k = Math.min(1, (t - t0) / ms);
        const e = k < 0.5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2;
        if (k < 1) {
          render(180 * e, { exact: true });
          raf = requestAnimationFrame(frame);
        } else {
          raf = null;
          render(180);
        }
      };
      raf = requestAnimationFrame(frame);
    },
    stop,
  };
}
