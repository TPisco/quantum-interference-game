/*
  Rendering helpers: circuit strip, histogram (as an accessible table), goal
  meter, single-qubit marginals and the "amplitude arrows" explainer.

  Accessibility rules followed here:
  - every SVG has role="img" and a full text alternative (aria-label);
  - numbers are always printed as text next to bars (bars are decoration);
  - the two paths differ by colour AND line style (upper: solid, lower: dashed);
  - target outcomes are marked with a text label, not colour alone.
*/

const SVG_NS = "http://www.w3.org/2000/svg";

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v === true ? "" : String(v));
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "text") node.textContent = v;
    else node.setAttribute(k, String(v));
  }
  for (const c of children.flat()) if (c) node.append(c);
  return node;
}

function gcd(a, b) {
  return b ? gcd(b, a % b) : a;
}

/** 135 -> "135° (3π/4)". */
export function angleText(deg) {
  const d = ((Math.round(Number(deg)) % 360) + 360) % 360;
  if (d === 0) return "0°";
  const g = gcd(d, 180);
  const num = d / g;
  const den = 180 / g;
  let pi;
  if (den === 1) pi = num === 1 ? "π" : `${num}π`;
  else pi = num === 1 ? `π/${den}` : `${num}π/${den}`;
  return `${d}° (${pi})`;
}

export const pct = (x, digits = 0) => `${(100 * Number(x)).toFixed(digits)}%`;

export function starsText(n, max = 3) {
  const s = Math.max(0, Math.min(max, Number(n) || 0));
  return "★".repeat(s) + "☆".repeat(max - s);
}

// ------------------------------------------------------------------ circuit

function stepActive(step, config) {
  return !step.toggle || Boolean(config[step.toggle]);
}

function stepName(level, s, config) {
  const q = level.qubit_names[s.qubits[0]];
  const both = s.qubits.map((i) => level.qubit_names[i]).join(" and ");
  switch (s.gate) {
    case "h": return `${s.label} on ${both}`;
    case "x": return `${s.label} on ${q}`;
    case "p": return `${s.label} on ${q}, φ = ${angleText(config[s.angle] ?? 0)}`;
    case "cp": return `${s.label}: control ${q}, target ${level.qubit_names[s.qubits[1]]}, φ = ${angleText(config[s.angle] ?? 0)}`;
    case "mystery": return `${s.label} on ${q}, value hidden`;
    case "cx": return `${s.label}: control ${q}, target ${level.qubit_names[s.qubits[1]]}`;
    case "diffuser": return `${s.label} on ${both}`;
    default: return s.label;
  }
}

export function describeCircuit(level, config) {
  const parts = level.steps.map((s) => {
    let name = stepName(level, s, config);
    if (s.toggle) name += stepActive(s, config) ? " (on)" : " (switched off)";
    if (s.role === "player") name += " [you control this]";
    return name;
  });
  return `Circuit for level ${level.number}, starting from |0⟩: ${parts.join("; then ")}; then measure every qubit.`;
}

const INK = { text: "#e8ecf8", muted: "#b4bedb", wire: "#8a96bf", player: "#5ce1e6", mystery: "#c4a3ff", phase: "#ffb000" };

/** The circuit strip. compact: tighter geometry for narrow containers (qubit
 *  names sit above their |0⟩ instead of beside it). */
export function circuitSVG(level, config, { compact = false } = {}) {
  const n = level.num_qubits;
  const G = compact
    ? { colW: 76, x0: 56, half: 26, rowH: 80, wireX: 40, nameFont: 12, capFont: 11 }
    : { colW: 96, x0: 128, half: 30, rowH: 84, wireX: 126, nameFont: 15, capFont: 12 };
  const gx = (j) => G.x0 + G.colW * j + G.half + 4;
  const gy = (q) => 64 + G.rowH * q;
  const mx = gx(level.steps.length);
  const width = mx + 44;
  const height = gy(n - 1) + 56;
  const root = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": describeCircuit(level, config),
    "data-compact": String(compact),
  });

  for (let q = 0; q < n; q++) {
    const y = gy(q);
    if (compact) {
      root.append(
        svg("text", { x: 4, y: y - 14, fill: INK.text, "font-size": G.nameFont, "font-weight": 700, text: level.qubit_names[q] }),
        svg("text", { x: 4, y: y + 6, fill: INK.muted, "font-size": 14, "font-family": "monospace", text: "|0⟩" }),
      );
    } else {
      root.append(
        svg("text", { x: 8, y: y + 5, fill: INK.text, "font-size": G.nameFont, "font-weight": 700, text: level.qubit_names[q] }),
        svg("text", { x: 96, y: y + 6, fill: INK.muted, "font-size": 16, "font-family": "monospace", text: "|0⟩" }),
      );
    }
    root.append(svg("line", { x1: G.wireX, y1: y, x2: mx, y2: y, stroke: INK.wire, "stroke-width": 2 }));
  }

  const box = (x, y, label, look, { h = 44, w = 2 * G.half, size = 16 } = {}) => [
    svg("rect", {
      x: x - w / 2, y: y - h / 2, width: w, height: h, rx: 9, fill: look.fill, stroke: look.stroke,
      "stroke-width": look.player ? 3 : 2, "stroke-dasharray": look.dash,
    }),
    svg("text", {
      x, y: y + size * 0.36, "text-anchor": "middle", fill: look.active ? INK.text : INK.wire,
      "font-size": size, "font-weight": 700, "font-family": "monospace", text: label,
    }),
  ];

  level.steps.forEach((s, j) => {
    const x = gx(j);
    const active = stepActive(s, config);
    const player = s.role === "player";
    const mystery = s.gate === "mystery";
    const look = {
      active, player,
      stroke: !active ? INK.wire : mystery ? INK.mystery : player ? INK.player : INK.wire,
      fill: !active ? "#0e1530" : mystery ? "#2a1f4a" : player ? "#10334a" : "#232d55",
      dash: active ? null : "6 5",
    };
    const top = Math.min(...s.qubits);
    const bottom = Math.max(...s.qubits);
    root.append(svg("text", {
      x, y: gy(top) - 34, "text-anchor": "middle", fill: player ? INK.player : INK.muted,
      "font-size": G.capFont, "font-weight": player ? 700 : 400, text: s.short,
    }));
    const angleLabel = (y) => svg("text", {
      x, y, "text-anchor": "middle", fill: INK.phase, "font-size": 13, "font-weight": 700,
      text: `${Math.round(Number(config[s.angle] ?? 0))}°`,
    });

    if (s.gate === "cx") {
      const [c, t] = s.qubits;
      root.append(
        svg("line", { x1: x, y1: gy(c), x2: x, y2: gy(t) + 16, stroke: look.stroke, "stroke-width": 3 }),
        svg("circle", { cx: x, cy: gy(c), r: 7, fill: look.stroke }),
        svg("circle", { cx: x, cy: gy(t), r: 16, fill: look.fill, stroke: look.stroke, "stroke-width": 3 }),
        svg("line", { x1: x - 10, y1: gy(t), x2: x + 10, y2: gy(t), stroke: look.stroke, "stroke-width": 3 }),
        svg("line", { x1: x, y1: gy(t) - 10, x2: x, y2: gy(t) + 10, stroke: look.stroke, "stroke-width": 3 }),
      );
    } else if (s.gate === "cp") {
      const [c, t] = s.qubits;
      root.append(
        svg("line", { x1: x, y1: gy(c), x2: x, y2: gy(t) - 22, stroke: look.stroke, "stroke-width": 3, "stroke-dasharray": look.dash }),
        svg("circle", { cx: x, cy: gy(c), r: 7, fill: look.stroke }),
        ...box(x, gy(t), "P(φ)", look),
      );
      if (active) root.append(angleLabel(gy(t) + 40));
    } else if (s.gate === "diffuser") {
      const y = (gy(top) + gy(bottom)) / 2;
      root.append(...box(x, y, "D", look, { h: gy(bottom) - gy(top) + 44, size: 22 }));
    } else {
      const label = { h: "H", x: "X", p: "P(φ)", mystery: "θ ?" }[s.gate] ?? s.gate;
      for (const q of s.gate === "h" ? s.qubits : [s.qubits[0]]) {
        root.append(...box(x, gy(q), label, look, { size: s.gate === "h" || s.gate === "x" ? 20 : 16 }));
      }
      if (active && s.gate === "p") root.append(angleLabel(gy(s.qubits[0]) + 40));
    }
    if (!active) {
      root.append(svg("text", { x, y: gy(bottom) + 40, "text-anchor": "middle", fill: INK.muted, "font-size": 12, text: "off" }));
    }
  });

  for (let q = 0; q < n; q++) {
    const y = gy(q);
    root.append(
      svg("rect", { x: mx - 22, y: y - 20, width: 44, height: 40, rx: 8, fill: "#232d55", stroke: INK.text, "stroke-width": 2 }),
      svg("path", { d: `M ${mx - 13} ${y + 8} A 14 14 0 0 1 ${mx + 13} ${y + 8}`, fill: "none", stroke: INK.text, "stroke-width": 2 }),
      svg("line", { x1: mx, y1: y + 9, x2: mx + 9, y2: y - 10, stroke: INK.text, "stroke-width": 2 }),
    );
  }
  root.append(svg("text", {
    x: mx, y: gy(0) - 34, "text-anchor": "middle", fill: INK.muted, "font-size": G.capFont, text: "Measure",
  }));
  return root;
}

/** Small dial showing a phase as an arrow turned counter-clockwise by deg
 *  (same convention as the amplitude arrows). Decorative: the number is
 *  always printed next to it. */
export function phaseClock(deg) {
  const r = (Number(deg) * Math.PI) / 180;
  const x = 20 + 13 * Math.cos(r);
  const y = 20 - 13 * Math.sin(r);
  return svg("svg", { viewBox: "0 0 40 40", width: 36, height: 36, class: "ps-clock", "aria-hidden": "true" },
    svg("circle", { cx: 20, cy: 20, r: 17, fill: "none", stroke: "#34406b", "stroke-width": 2 }),
    svg("line", { x1: 20, y1: 20, x2: 37, y2: 20, stroke: "#34406b", "stroke-width": 1.5, "stroke-dasharray": "2 2" }),
    svg("line", { x1: 20, y1: 20, x2: x, y2: y, stroke: INK.phase, "stroke-width": 3.5, "stroke-linecap": "round" }),
    svg("circle", { cx: 20, cy: 20, r: 3, fill: INK.phase }));
}

// ---------------------------------------------------------------- histogram

export function histogramTable(res) {
  const where = res.source?.name ?? "simulator";
  const table = el("table", { class: "ps-hist" },
    el("caption", { text: `Measured probabilities: ${res.shots} shots on ${where}` }),
    el("thead", {}, el("tr", {},
      el("th", { scope: "col", text: "Outcome" }),
      el("th", { scope: "col", text: "Histogram" }),
      el("th", { scope: "col", class: "ps-hist__num", text: "Measured" }),
      el("th", { scope: "col", class: "ps-hist__num", text: "Theory" }),
    )),
  );
  const body = el("tbody");
  for (const o of res.outcomes) {
    const fill = el("div", {
      class: `ps-bar__fill${o.is_target ? " ps-bar__fill--target" : ""}`,
      style: `width:${(100 * o.measured).toFixed(1)}%`,
    });
    const bar = el("div", { class: "ps-bar", "aria-hidden": "true" }, fill,
      el("div", { class: "ps-bar__ci", style: `left:${(100 * o.ci[0]).toFixed(1)}%;width:${(100 * (o.ci[1] - o.ci[0])).toFixed(1)}%` }));
    if (typeof o.theory === "number") {
      bar.append(el("div", { class: "ps-bar__theory", style: `left:${(100 * o.theory).toFixed(1)}%` }));
    }
    const lo = pct(o.ci[0]);
    const hi = pct(o.ci[1]);
    body.append(el("tr", {},
      el("th", { scope: "row", class: "ps-hist__outcome" }, o.label,
        o.is_target ? el("span", { class: "ps-hist__target", text: "◎ target" }) : null),
      el("td", { class: "ps-hist__barcell" }, bar),
      el("td", { class: "ps-hist__num" }, `${pct(o.measured, 1)}`,
        el("span", { class: "ps-sr", text: ` (95% range ${lo} to ${hi}, ${o.count} counts)` })),
      el("td", { class: "ps-hist__num", text: typeof o.theory === "number" ? pct(o.theory, 1) : "hidden" }),
    ));
  }
  table.append(body);
  const key = el("p", { class: "ps-note" },
    "Bars: measured share of shots. White line: 95% range from shot noise. Dotted line: exact theory.");
  return el("div", {}, table, key);
}

export function goalMeter(res) {
  const t = res.target;
  const value = Number(t.value);
  const met = Boolean(res.feedback?.solved);
  const wrap = el("div", {});
  wrap.append(
    el("p", { class: "ps-goalmeter__label" },
      el("span", { text: `Goal: ${t.short}` }),
      el("span", { text: `${met ? "✓ met" : "✗ not yet"}: ${pct(value, 1)}` })),
    el("div", {
      class: "ps-goalmeter__track", role: "img",
      "aria-label": `Target value ${pct(value, 1)}; goal ${t.op === ">=" ? "at least" : "at most"} ${pct(t.threshold)}. ${met ? "Goal met." : "Goal not met yet."}`,
    },
    el("div", { class: "ps-goalmeter__fill", "data-met": String(met), style: `width:${(100 * value).toFixed(1)}%` }),
    el("div", { class: "ps-goalmeter__threshold", style: `left:${(100 * t.threshold).toFixed(1)}%` })),
  );
  return wrap;
}

export function marginalsTable(res) {
  if (!res.marginals?.length) return null;
  const table = el("table", { class: "ps-hist ps-marg" },
    el("caption", { text: "Each qubit on its own (ignoring the other)" }),
    el("thead", {}, el("tr", {},
      el("th", { scope: "col", text: "Qubit" }),
      el("th", { scope: "col", class: "ps-hist__num", text: "Measured P(1)" }),
      el("th", { scope: "col", class: "ps-hist__num", text: "Theory P(1)" }))));
  const body = el("tbody");
  for (const m of res.marginals) {
    body.append(el("tr", {},
      el("th", { scope: "row", text: m.name }),
      el("td", { class: "ps-hist__num", text: pct(m.measured["1"], 1) }),
      el("td", { class: "ps-hist__num", text: res.revealed ? pct(m.theory["1"], 1) : "hidden" })));
  }
  table.append(body);
  return el("div", {}, table, res.marginal_note ? el("p", { class: "ps-note", text: res.marginal_note }) : null);
}

// ------------------------------------------------------------------ arrows

const ARM = {
  upper: { color: "#4ea8ff", dash: null, name: "upper path" },
  lower: { color: "#ffb000", dash: "7 5", name: "lower path" },
};

function direction(re, im) {
  const deg = ((Math.atan2(im, re) * 180) / Math.PI + 360) % 360;
  return Math.round(deg) % 360;
}

function describeArrows(o) {
  const arrows = o.arrows.map((a) => {
    const len = Math.hypot(a.re, a.im);
    return `${ARM[a.arm].name} arrow, length ${len.toFixed(2)}, pointing ${direction(a.re, a.im)}°`;
  });
  const sumLen = Math.hypot(o.sum.re, o.sum.im);
  const kind = interferenceKind(o);
  return `Outcome ${o.label}: ${o.arrows.length} path arrow${o.arrows.length === 1 ? "" : "s"}. ${arrows.join("; ")}. ` +
    `Added head to tail they give length ${sumLen.toFixed(2)}, so the quantum probability is ${pct(o.theory)}. ` +
    `Adding probabilities classically would give ${pct(o.classical)}. Interference: ${kind}.`;
}

let svgUid = 0;

/** reach: the longest head-to-tail chain among all outcomes; the dial circle is
 *  drawn at that length (labelled with reach² as a probability) so small arrows
 *  stay readable while every card keeps the same scale. */
export function arrowSVG(o, reach = 1) {
  const uid = `psa${++svgUid}`;
  const C = 120;
  const R = 92 / Math.max(reach, 0.05);
  const root = svg("svg", { viewBox: "0 0 240 240", role: "img", "aria-label": describeArrows(o) });
  const defs = svg("defs");
  for (const [id, color] of [["u", ARM.upper.color], ["l", ARM.lower.color], ["s", "#ffffff"]]) {
    defs.append(svg("marker", {
      id: `${uid}${id}`, viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 5, markerHeight: 5, orient: "auto-start-reverse",
    }, svg("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: color })));
  }
  root.append(defs,
    svg("circle", { cx: C, cy: C, r: 92, fill: "none", stroke: "#34406b", "stroke-width": 1.5, "stroke-dasharray": "3 4" }),
    svg("line", { x1: C - 98, y1: C, x2: C + 98, y2: C, stroke: "#26304f", "stroke-width": 1 }),
    svg("line", { x1: C, y1: C - 98, x2: C, y2: C + 98, stroke: "#26304f", "stroke-width": 1 }),
    svg("text", { x: C + 90, y: C - 84, "text-anchor": "end", fill: "#8a96bf", "font-size": 11, text: pct(reach * reach) }),
  );

  const sumLen = Math.hypot(o.sum.re, o.sum.im);
  if (sumLen > 0.03) {
    root.append(
      svg("line", {
        x1: C, y1: C, x2: C + R * o.sum.re, y2: C - R * o.sum.im,
        stroke: "#ffffff", "stroke-opacity": 0.28, "stroke-width": 12, "stroke-linecap": "round",
      }),
      svg("line", {
        x1: C, y1: C, x2: C + R * o.sum.re, y2: C - R * o.sum.im,
        stroke: "#ffffff", "stroke-width": 2, "marker-end": `url(#${uid}s)`,
      }),
    );
  } else {
    root.append(svg("circle", { cx: C, cy: C, r: 9, fill: "none", stroke: "#ffffff", "stroke-width": 2.5 }));
  }

  let x = 0;
  let y = 0;
  o.arrows.forEach((a, k) => {
    const x2 = x + a.re;
    const y2 = y + a.im;
    // Shift later arrows sideways a little so arrows that double back stay visible.
    const len = Math.hypot(a.re, a.im) || 1;
    const off = 5 * k;
    const ox = (-a.im / len) * off;
    const oy = (a.re / len) * off;
    const arm = ARM[a.arm];
    root.append(svg("line", {
      x1: C + R * x + ox, y1: C - R * y - oy, x2: C + R * x2 + ox, y2: C - R * y2 - oy,
      stroke: arm.color, "stroke-width": 4, "stroke-dasharray": arm.dash, "marker-end": `url(#${uid}${a.arm[0]})`,
    }));
    x = x2;
    y = y2;
  });
  return root;
}

/** Longest head-to-tail chain of arrows over all outcomes of a result. */
export function arrowReach(outcomes) {
  return Math.max(...outcomes.map((o) => o.arrows.reduce((t, a) => t + Math.hypot(a.re, a.im), 0)), 0.05);
}

function interferenceKind(o) {
  if (o.interference > 1e-6) return "constructive";
  if (o.interference < -1e-6) return "destructive";
  if (o.arrows.length === 0) return "no path reaches this outcome";
  if (o.arrows.length < 2) return "none (only one path)";
  return o.arrows.length === 2 ? "none (arrows at right angles)" : "none (cross terms cancel)";
}

export function arrowCard(o, reach = 1) {
  const kind = interferenceKind(o);
  const sign = o.interference > 1e-6 ? "+" : "";
  return el("figure", { class: "ps-arrowcard", "data-target": String(Boolean(o.is_target)) },
    arrowSVG(o, reach),
    el("figcaption", {},
      el("span", { class: "ps-arrowcard__title" }, o.label, o.is_target ? " ◎" : ""),
      el("dl", {},
        el("dt", { text: "Paths" }), el("dd", { text: String(o.arrows.length) }),
        el("dt", { text: "Classical" }), el("dd", { text: pct(o.classical) }),
        el("dt", { text: "Quantum" }), el("dd", { text: pct(o.theory) }),
        el("dt", { text: "Interference" }), el("dd", { text: `${sign}${pct(o.interference)}` }),
      ),
      el("span", { class: "ps-note", text: kind })),
  );
}

export function arrowKey() {
  const sample = (arm) => svg("svg", { width: 34, height: 10, "aria-hidden": "true" },
    svg("line", { x1: 2, y1: 5, x2: 32, y2: 5, stroke: arm === "sum" ? "#ffffff" : ARM[arm].color, "stroke-width": arm === "sum" ? 3 : 4, "stroke-dasharray": arm === "lower" ? "7 5" : null }));
  return el("p", { class: "ps-key" },
    el("span", {}, sample("upper"), " upper path: first qubit 0 after the split (solid)"),
    el("span", {}, sample("lower"), " lower path: first qubit 1 (dashed)"),
    el("span", {}, sample("sum"), " sum = what you measure"),
    el("span", {}, "dotted circle: the longest possible sum, labelled with its probability"));
}

// ------------------------------------------------------- interference curve

/** Goal value against the phase φ (0° to 360°), for the gates as they are set now.
 *  The goal region is shaded, the curve is drawn solid, and a marker shows the
 *  current φ. A text sentence carries the same information for screen readers. */
export function interferenceCurve(sw) {
  const W = 360, H = 180, L = 46, R = 14, T = 12, B = 32;
  const pw = W - L - R, ph = H - T - B;
  const x = (deg) => L + (pw * deg) / 360;
  const y = (v) => T + ph * (1 - v);
  const t = sw.target;
  const goalWord = t.op === ">=" ? "at least" : "at most";
  const measure = t.short.split(/ (?=[≥≤])/)[0];
  const met = (v) => (t.op === ">=" ? v >= t.threshold : v <= t.threshold);

  const band = t.op === ">="
    ? svg("rect", { x: L, y: y(1), width: pw, height: y(t.threshold) - y(1), class: "ps-curve__goal" })
    : svg("rect", { x: L, y: y(t.threshold), width: pw, height: y(0) - y(t.threshold), class: "ps-curve__goal" });
  const grid = [];
  for (const v of [0, 0.5, 1]) {
    grid.push(svg("line", { x1: L, x2: L + pw, y1: y(v), y2: y(v), class: "ps-curve__grid" }),
      svg("text", { x: L - 6, y: y(v) + 4, "text-anchor": "end", class: "ps-curve__tick", text: `${v * 100}%` }));
  }
  for (const d of [0, 90, 180, 270, 360]) {
    grid.push(svg("line", { x1: x(d), x2: x(d), y1: T, y2: T + ph, class: "ps-curve__grid" }),
      svg("text", { x: x(d), y: H - 10, "text-anchor": "middle", class: "ps-curve__tick", text: `${d}°` }));
  }
  const line = sw.points.map((p, i) => `${i ? "L" : "M"}${x(p.phi).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const cur = sw.current;
  const marker = svg("g", { class: "ps-curve__marker", "data-met": String(met(cur.value)) },
    svg("line", { x1: x(cur.phi), x2: x(cur.phi), y1: T, y2: T + ph, class: "ps-curve__now" }),
    svg("circle", { cx: x(cur.phi), cy: y(cur.value), r: 6 }));

  const now = `At φ = ${angleText(cur.phi)}: ${measure} = ${pct(cur.value, 1)} (${met(cur.value) ? "goal met" : "goal not met"}).`;
  const shape = sw.flat
    ? `The curve is flat at ${pct(cur.value, 1)}: with the gates as they are, the phase changes nothing, so there is no interference.`
    : `It swings between ${pct(Math.min(...sw.points.map((p) => p.value)), 0)} and ${pct(Math.max(...sw.points.map((p) => p.value)), 0)}; the best phase is φ = ${angleText(sw.best.phi)} (${pct(sw.best.value, 1)}).`;
  const label = `Interference curve: ${measure} against the phase φ from 0° to 360°, goal ${goalWord} ${pct(t.threshold)}. ${now} ${shape}`;

  const chart = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "ps-curve__svg", role: "img", "aria-label": label },
    band, ...grid,
    svg("text", { x: L + pw - 6, y: (t.op === ">=" ? y(1) : y(0)) + (t.op === ">=" ? 14 : -5), "text-anchor": "end", class: "ps-curve__goal-label", text: "goal" }),
    svg("path", { d: line, class: "ps-curve__line" }),
    marker);
  return el("div", { class: "ps-curve__body" }, chart,
    el("p", { class: "ps-curve__now-text", "aria-hidden": "true" }, now),
    el("p", { class: "ps-note", "aria-hidden": "true" }, shape));
}
