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

export function describeCircuit(level, config) {
  const parts = level.steps.map((s) => {
    const q = level.qubit_names[s.qubits[0]];
    let name;
    if (s.gate === "h") name = `${s.label} on ${q}`;
    else if (s.gate === "p") name = `${s.label} on ${q}, φ = ${angleText(config[s.angle] ?? 0)}`;
    else if (s.gate === "mystery") name = `${s.label} on ${q}, value hidden`;
    else if (s.gate === "cx") name = `${s.label}: control ${q}, target ${level.qubit_names[s.qubits[1]]}`;
    else name = s.label;
    if (s.toggle) name += stepActive(s, config) ? " (on)" : " (switched off)";
    if (s.role === "player") name += " [you control this]";
    return name;
  });
  return `Circuit for level ${level.number}, starting from |0⟩: ${parts.join("; then ")}; then measure every qubit.`;
}

export function circuitSVG(level, config) {
  const n = level.num_qubits;
  const colW = 96;
  const x0 = 150;
  const rowH = 84;
  const y0 = 64;
  const gx = (j) => x0 + colW * j + 32;
  const gy = (q) => y0 + rowH * q;
  const mx = gx(level.steps.length);
  const width = mx + 60;
  const height = gy(n - 1) + 52;
  const root = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": describeCircuit(level, config),
  });

  for (let q = 0; q < n; q++) {
    root.append(
      svg("text", { x: 8, y: gy(q) + 5, fill: "#e8ecf8", "font-size": 15, "font-weight": 700, text: level.qubit_names[q] }),
      svg("text", { x: 96, y: gy(q) + 6, fill: "#b4bedb", "font-size": 16, "font-family": "monospace", text: "|0⟩" }),
      svg("line", { x1: 126, y1: gy(q), x2: mx, y2: gy(q), stroke: "#8a96bf", "stroke-width": 2 }),
    );
  }

  level.steps.forEach((s, j) => {
    const x = gx(j);
    const active = stepActive(s, config);
    const player = s.role === "player";
    const mystery = s.gate === "mystery";
    const stroke = !active ? "#8a96bf" : mystery ? "#c4a3ff" : player ? "#5ce1e6" : "#8a96bf";
    const fill = !active ? "#0e1530" : mystery ? "#2a1f4a" : player ? "#10334a" : "#232d55";
    const dash = active ? null : "6 5";
    const captionY = s.gate === "cx" ? gy(0) - 34 : gy(s.qubits[0]) - 34;
    root.append(svg("text", {
      x, y: captionY, "text-anchor": "middle", fill: player ? "#5ce1e6" : "#b4bedb",
      "font-size": 12, "font-weight": player ? 700 : 400, text: s.short,
    }));

    if (s.gate === "cx") {
      const [c, t] = s.qubits;
      root.append(
        svg("line", { x1: x, y1: gy(c), x2: x, y2: gy(t) + 16, stroke, "stroke-width": 3 }),
        svg("circle", { cx: x, cy: gy(c), r: 7, fill: stroke }),
        svg("circle", { cx: x, cy: gy(t), r: 16, fill, stroke, "stroke-width": 3 }),
        svg("line", { x1: x - 10, y1: gy(t), x2: x + 10, y2: gy(t), stroke, "stroke-width": 3 }),
        svg("line", { x1: x, y1: gy(t) - 10, x2: x, y2: gy(t) + 10, stroke, "stroke-width": 3 }),
      );
      return;
    }

    const y = gy(s.qubits[0]);
    root.append(svg("rect", {
      x: x - 30, y: y - 22, width: 60, height: 44, rx: 9, fill, stroke,
      "stroke-width": player ? 3 : 2, "stroke-dasharray": dash,
    }));
    let label = "H";
    if (s.gate === "p") label = "P(φ)";
    if (mystery) label = "θ ?";
    root.append(svg("text", {
      x, y: y + 6, "text-anchor": "middle", fill: active ? "#e8ecf8" : "#8a96bf",
      "font-size": s.gate === "h" ? 20 : 16, "font-weight": 700, "font-family": "monospace", text: label,
    }));
    if (!active) {
      root.append(svg("text", { x, y: y + 40, "text-anchor": "middle", fill: "#b4bedb", "font-size": 12, text: "off" }));
    } else if (s.gate === "p") {
      const deg = Math.round(Number(config[s.angle] ?? 0));
      root.append(svg("text", {
        x, y: y + 40, "text-anchor": "middle", fill: "#ffb000", "font-size": 13, "font-weight": 700, text: `${deg}°`,
      }));
    }
  });

  for (let q = 0; q < n; q++) {
    const y = gy(q);
    root.append(
      svg("rect", { x: mx - 22, y: y - 20, width: 44, height: 40, rx: 8, fill: "#232d55", stroke: "#e8ecf8", "stroke-width": 2 }),
      svg("path", { d: `M ${mx - 13} ${y + 8} A 14 14 0 0 1 ${mx + 13} ${y + 8}`, fill: "none", stroke: "#e8ecf8", "stroke-width": 2 }),
      svg("line", { x1: mx, y1: y + 9, x2: mx + 9, y2: y - 10, stroke: "#e8ecf8", "stroke-width": 2 }),
    );
  }
  root.append(svg("text", {
    x: mx, y: gy(0) - 34, "text-anchor": "middle", fill: "#b4bedb", "font-size": 12, text: "Measure",
  }));
  return root;
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
  return el("div", {}, table, el("p", { class: "ps-note", text:
    "Look at the photon alone: it stays near 50% whatever you do. Any interference pattern can only show up in the joint outcomes above." }));
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
    el("span", {}, sample("upper"), " upper path (solid)"),
    el("span", {}, sample("lower"), " lower path, where phases act (dashed)"),
    el("span", {}, sample("sum"), " sum = what you measure"),
    el("span", {}, "dotted circle: the longest possible sum, labelled with its probability"));
}
