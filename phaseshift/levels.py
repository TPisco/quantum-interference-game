"""Level definitions for Phase Shift.

A level is pure data: the gates on the wire (fixed or player-controlled), the
controls the player may change, the target condition on the measured
probabilities, and the hint text. ``circuits.build_circuit`` turns a level plus
a player configuration into a Qiskit circuit; ``game`` judges the result.

Conventions
-----------
* Angles are in DEGREES everywhere in the public API (sliders, configs).
* Outcome keys are Qiskit bitstrings: the rightmost character is qubit 0.
  For the two-qubit level, key ``"10"`` means qubit 1 (detector) = 1 and
  qubit 0 (photon) = 0.
* Every level starts with an H on qubit 0, which splits the qubit into two
  "paths": the *upper path* (qubit 0 = |0>) and the *lower path* (qubit 0 = |1>).
  Phase gates act on the lower path only (Kickback and Amplifier use a
  controlled phase, which acts only when both qubits are 1).

To add a level, append a ``Level`` to ``LEVELS`` (see docs/DEVELOPER_GUIDE.md).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Control:
    """Something the player can change."""

    id: str
    kind: str  # "angle" (slider in degrees) or "toggle" (gate on/off)
    label: str
    description: str
    default: Any
    min: float = 0.0
    max: float = 345.0
    step: float = 15.0

    def public(self) -> dict[str, Any]:
        out = {"id": self.id, "kind": self.kind, "label": self.label,
               "description": self.description, "default": self.default}
        if self.kind == "angle":
            out.update(min=self.min, max=self.max, step=self.step)
        return out


@dataclass(frozen=True)
class Step:
    """One gate on the wire.

    gate:     "h" (on every listed qubit), "x", "p" (phase gate P(angle)),
              "cp" (controlled phase), "cx", "mystery" (hidden phase) or
              "diffuser" (Grover's reflection about the average, two qubits).
    qubits:   target qubit(s); for "cx" and "cp" (control, target).
    angle:    id of the angle control for a player phase gate, or None.
    toggle:   id of a toggle control; the gate is present only when it is on.
    label:    descriptive name (used in code comments and screen-reader text).
    short:    one-word caption above the gate in the circuit strip.
    role:     "fixed" (part of the level) or "player" (you control it).
    """

    gate: str
    qubits: tuple[int, ...]
    label: str
    angle: str | None = None
    toggle: str | None = None
    fixed_angle: float | None = None
    short: str = ""

    @property
    def role(self) -> str:
        return "player" if (self.angle or self.toggle) else "fixed"

    def public(self) -> dict[str, Any]:
        return {"gate": self.gate, "qubits": list(self.qubits), "label": self.label,
                "short": self.short or self.label, "angle": self.angle, "toggle": self.toggle,
                "role": self.role}


@dataclass(frozen=True)
class Target:
    """Win condition: the summed probability of ``outcomes`` compared to ``threshold``."""

    outcomes: tuple[str, ...]
    op: str  # ">=" or "<="
    threshold: float
    description: str
    short: str

    def met(self, value: float) -> bool:
        return value >= self.threshold if self.op == ">=" else value <= self.threshold

    def value(self, probabilities: dict[str, float]) -> float:
        return float(sum(probabilities.get(k, 0.0) for k in self.outcomes))

    def public(self) -> dict[str, Any]:
        return {"outcomes": list(self.outcomes), "op": self.op, "threshold": self.threshold,
                "description": self.description, "short": self.short}


@dataclass(frozen=True)
class Level:
    id: str
    number: int
    title: str
    concept: str
    tagline: str
    story: str
    num_qubits: int
    qubit_names: tuple[str, ...]
    steps: tuple[Step, ...]
    controls: tuple[Control, ...]
    target: Target
    hints: tuple[str, ...]
    learn: str
    par_runs: int
    outcome_names: dict[str, str] = field(default_factory=dict)
    # Shown under the per-qubit table on multi-qubit levels; empty = no table.
    marginal_note: str = ""

    def control(self, cid: str) -> Control:
        for c in self.controls:
            if c.id == cid:
                return c
        raise KeyError(cid)

    def default_config(self) -> dict[str, Any]:
        return {c.id: c.default for c in self.controls}

    def outcome_keys(self) -> list[str]:
        n = self.num_qubits
        return [format(i, f"0{n}b") for i in range(2**n)]

    def outcome_label(self, key: str) -> str:
        return self.outcome_names.get(key, f"|{key}⟩")

    def public(self) -> dict[str, Any]:
        """JSON-safe description for the UI (never includes hidden values)."""
        return {
            "id": self.id, "number": self.number, "title": self.title, "concept": self.concept,
            "tagline": self.tagline, "story": self.story, "num_qubits": self.num_qubits,
            "qubit_names": list(self.qubit_names),
            "steps": [s.public() for s in self.steps],
            "controls": [c.public() for c in self.controls],
            "target": self.target.public(), "hints": list(self.hints), "learn": self.learn,
            "par_runs": self.par_runs, "default_config": self.default_config(),
            "outcomes": [{"key": k, "label": self.outcome_label(k)} for k in self.outcome_keys()],
            "has_mystery": any(s.gate == "mystery" for s in self.steps),
        }


PHASE = Control(
    id="phi", kind="angle", label="Phase φ on the lower path",
    description="Rotates the arrow (phase) of the lower path. 180° turns + into −.",
    default=0.0,
)

# --------------------------------------------------------------------------
# Level 1 - phase is invisible until the paths recombine
# --------------------------------------------------------------------------
INVISIBLE_INK = Level(
    id="invisible-ink",
    number=1,
    title="Invisible Ink",
    concept="Superposition and phase",
    tagline="Paint a phase on one path. Can a measurement see it?",
    story=(
        "A Hadamard gate (H) acts like a beam splitter: your qubit now travels the upper "
        "path |0⟩ and the lower path |1⟩ at the same time. You can paint a phase φ on the "
        "lower path with a phase gate. Your goal: make the detector read |1⟩ at least 90% "
        "of the time. First try the phase alone, then decide whether to recombine the paths "
        "with a second H."
    ),
    num_qubits=1,
    qubit_names=("qubit",),
    steps=(
        Step("h", (0,), "Split (H)", short="Split"),
        Step("p", (0,), "Phase P(φ)", angle="phi", short="Phase"),
        Step("h", (0,), "Recombine (H)", toggle="recombine", short="Recombine"),
    ),
    controls=(
        PHASE,
        Control(
            id="recombine", kind="toggle", label="Recombine the paths (second H)",
            description="A second Hadamard makes the two paths meet so their amplitudes can add or cancel.",
            default=False,
        ),
    ),
    target=Target(("1",), ">=", 0.90,
                  "Measure |1⟩ at least 90% of the time.", "P(|1⟩) ≥ 90%"),
    hints=(
        "Run the circuit with the recombiner off at two different phases. Does the histogram change?",
        "Measurement only sees how long each amplitude arrow is, not which way it points. "
        "Interference needs two arrows landing on the same outcome: switch on the second H.",
        "With both H gates on, P(|1⟩) = sin²(φ/2). Which angle makes that equal to 1?",
    ),
    learn=(
        "A phase is real but invisible on its own: P(φ) only rotates the lower path's arrow, "
        "and a measurement sees arrow lengths, so every φ gives 50/50. The second H sends both "
        "paths to both outcomes. Now two arrows land on each outcome and add (constructive) or "
        "cancel (destructive). φ = 180° flips the lower arrow, so |0⟩ cancels and |1⟩ doubles."
    ),
    par_runs=4,
)

# --------------------------------------------------------------------------
# Level 2 - destructive interference + phase estimation (hidden phase)
# --------------------------------------------------------------------------
DARK_PORT = Level(
    id="dark-port",
    number=2,
    title="Dark Port",
    concept="Interference as a phase detector",
    tagline="Cancel a mystery phase so detector |1⟩ goes dark.",
    story=(
        "A mystery sample sits on the lower path and adds an unknown phase θ. This is an "
        "interferometer: both paths are already recombined. Dial a compensating phase φ so "
        "that the amplitudes for |1⟩ cancel and that detector goes dark (at most 5% of the "
        "time). Every run tells you something about θ. Can you find it in two runs?"
    ),
    num_qubits=1,
    qubit_names=("qubit",),
    steps=(
        Step("h", (0,), "Split (H)", short="Split"),
        Step("mystery", (0,), "Mystery sample θ", short="Mystery"),
        Step("p", (0,), "Your phase P(φ)", angle="phi", short="Your phase"),
        Step("h", (0,), "Recombine (H)", short="Recombine"),
    ),
    controls=(PHASE,),
    target=Target(("1",), "<=", 0.05,
                  "Make detector |1⟩ go dark: measure |1⟩ at most 5% of the time.",
                  "P(|1⟩) ≤ 5%"),
    hints=(
        "Start with φ = 0 and run once. How bright is detector |1⟩?",
        "For this interferometer P(|1⟩) = sin²(Δ/2), where Δ = θ + φ is the phase left "
        "between the two paths. A brightness of 50% means Δ = ±90°; 100% means Δ = 180°.",
        "Brightness tells you how far you are, not which way. Turn φ by your estimate of Δ "
        "in one direction; if it got brighter, go the other way.",
    ),
    learn=(
        "Interference turns an invisible phase into a measurable brightness: "
        "P(|1⟩) = sin²((θ + φ)/2). When φ = −θ the two arrows for |1⟩ point in opposite "
        "directions and cancel exactly: a 'dark port'. Interferometers such as LIGO and "
        "quantum sensors measure tiny phase shifts this way."
    ),
    par_runs=2,
)

# --------------------------------------------------------------------------
# Level 3 - which-path information kills interference; erasing it restores it
# --------------------------------------------------------------------------
ERASER = Level(
    id="eraser",
    number=3,
    title="Which-Path Eraser",
    concept="Entanglement and the quantum eraser",
    tagline="A detector spies on the paths. Erase what it knows.",
    story=(
        "Someone bolted a which-path detector onto your interferometer: a CNOT copies "
        "'which path?' into a second qubit. Now the photon and the detector are entangled "
        "and the interference is gone. You cannot remove the detector, but you can choose "
        "how to read it. Goal: make the photon and the detector DISAGREE (outcomes 01 or 10) "
        "at least 90% of the time."
    ),
    num_qubits=2,
    qubit_names=("photon", "detector"),
    steps=(
        Step("h", (0,), "Split (H)", short="Split"),
        Step("cx", (0, 1), "Which-path detector (CNOT)", short="Detector"),
        Step("p", (0,), "Phase P(φ)", angle="phi", short="Phase"),
        Step("h", (0,), "Recombine (H)", short="Recombine"),
        Step("h", (1,), "Eraser (H on detector)", toggle="eraser", short="Eraser"),
    ),
    controls=(
        PHASE,
        Control(
            id="eraser", kind="toggle", label="Erase which-path info (H on detector)",
            description="Measure the detector in the ± basis, which scrambles the record of which path was taken.",
            default=False,
        ),
    ),
    target=Target(("01", "10"), ">=", 0.90,
                  "Make photon and detector disagree (01 or 10) at least 90% of the time.",
                  "P(disagree) ≥ 90%"),
    hints=(
        "With the eraser off, try two different phases. Does anything change?",
        "The detector holds a record of the path. Paths that can be told apart cannot "
        "interfere. Switch on the eraser so the record no longer says which path.",
        "With the eraser on, P(disagree) = sin²(φ/2). Look at the photon on its own too: "
        "it stays 50/50. The interference now lives in the correlation.",
    ),
    learn=(
        "The CNOT entangles photon and detector, so each path leaves a different mark on the "
        "detector. Distinguishable paths do not interfere: one arrow per outcome, 25% each. "
        "The eraser H sends both marks to both detector outcomes, so two arrows land on every "
        "joint outcome again and interfere. The photon alone still looks 50/50; the pattern "
        "only appears when you compare it with the detector."
    ),
    par_runs=4,
    outcome_names={
        "00": "photon 0 · detector 0",
        "01": "photon 1 · detector 0",
        "10": "photon 0 · detector 1",
        "11": "photon 1 · detector 1",
    },
    marginal_note=(
        "Look at the photon alone: it stays near 50% whatever you do. Any interference "
        "pattern can only show up in the joint outcomes above."
    ),
)

# --------------------------------------------------------------------------
# Level 4 - phase kickback: the phase shows up on the qubit it was not "on"
# --------------------------------------------------------------------------
KICKBACK = Level(
    id="kickback",
    number=4,
    title="Kickback",
    concept="Phase kickback",
    tagline="Put a phase on the target. Watch the control react.",
    story=(
        "Two qubits now. The control goes through the same split and recombine as in level 1, "
        "but your phase gate is a controlled phase CP(φ): it adds φ only when the control AND "
        "the target are both 1. The target starts in |0⟩, and you may flip it to |1⟩ with an "
        "X gate. Goal: make the control qubit read 1 at least 90% of the time."
    ),
    num_qubits=2,
    qubit_names=("control", "target"),
    steps=(
        Step("h", (0,), "Split the control (H)", short="Split"),
        Step("x", (1,), "Flip the target (X)", toggle="flip", short="Flip"),
        Step("cp", (0, 1), "Controlled phase CP(φ)", angle="phi", short="C-phase"),
        Step("h", (0,), "Recombine the control (H)", short="Recombine"),
    ),
    controls=(
        Control(
            id="phi", kind="angle", label="Controlled phase φ",
            description="Added to the amplitude only when control and target are both 1.",
            default=0.0,
        ),
        Control(
            id="flip", kind="toggle", label="Flip the target to |1⟩ (X gate)",
            description="An X gate on the target before the controlled phase.",
            default=False,
        ),
    ),
    target=Target(("01", "11"), ">=", 0.90,
                  "Make the control qubit read 1 at least 90% of the time.",
                  "P(control = 1) ≥ 90%"),
    hints=(
        "Set φ = 180° and run with the flip off. Did the control notice the phase?",
        "A controlled phase only acts on the part of the state where BOTH qubits are 1. "
        "With the target in |0⟩ there is no such part. Switch on the X so the target is |1⟩.",
        "With the target in |1⟩, CP(φ) acts exactly like P(φ) on the control: "
        "P(control = 1) = sin²(φ/2).",
    ),
    learn=(
        "A controlled phase has no owner: diag(1, 1, 1, e^iφ) treats both qubits the same. "
        "When the target sits in |1⟩, the phase factors out and lands on the control's lower "
        "path, and the second H turns it into a measurable bit. The target never changes. "
        "This phase kickback is how Deutsch-Jozsa, phase estimation and Shor's algorithm read "
        "a hidden function: they put the answer into a phase, then let interference report it."
    ),
    par_runs=3,
    outcome_names={
        "00": "control 0 · target 0",
        "01": "control 1 · target 0",
        "10": "control 0 · target 1",
        "11": "control 1 · target 1",
    },
    marginal_note=(
        "Once you flip it, the target reads 1 every single time: the controlled phase never "
        "changed it. All the action shows up on the control."
    ),
)

# --------------------------------------------------------------------------
# Level 5 - Grover search on two qubits: amplitude amplification
# --------------------------------------------------------------------------
AMPLIFIER = Level(
    id="amplifier",
    number=5,
    title="Amplifier",
    concept="Amplitude amplification (Grover search)",
    tagline="Mark the prize with a phase, then make it loud.",
    story=(
        "Four doors, |00⟩ to |11⟩, and the prize is behind |11⟩. Two H gates open all four "
        "at once, 25% each. An oracle can mark the prize door with a phase φ, and a diffuser "
        "reflects every amplitude about the average. Goal: find the prize with one oracle "
        "query, measuring |11⟩ at least 90% of the time."
    ),
    num_qubits=2,
    qubit_names=("bit 0", "bit 1"),
    steps=(
        Step("h", (0, 1), "Spread over all four doors (H on both)", short="Spread"),
        Step("cp", (0, 1), "Oracle: phase φ on door |11⟩", angle="phi", short="Oracle"),
        Step("diffuser", (0, 1), "Diffuser (reflect about the average)", toggle="diffuser",
             short="Diffuser"),
    ),
    controls=(
        Control(
            id="phi", kind="angle", label="Oracle phase φ on door |11⟩",
            description="Rotates the arrow of the |11⟩ door only. 180° flips its sign.",
            default=0.0,
        ),
        Control(
            id="diffuser", kind="toggle", label="Diffuser (reflect about the average)",
            description="Sends every door to every door, so four paths meet on each outcome.",
            default=False,
        ),
    ),
    target=Target(("11",), ">=", 0.90,
                  "Find the prize: measure |11⟩ at least 90% of the time.",
                  "P(|11⟩) ≥ 90%"),
    hints=(
        "Turn the oracle phase and run with the diffuser off. Do the doors change?",
        "The oracle only rotates one arrow, and a measurement cannot see directions. Switch "
        "on the diffuser so four paths land on every door and interfere.",
        "With the diffuser on, P(|11⟩) = (10 − 6 cos φ)/16. It is largest when the marked "
        "arrow points the opposite way to the others.",
    ),
    learn=(
        "The diffuser replaces each amplitude by 2 × average − amplitude. Marking |11⟩ with "
        "φ = 180° gives amplitudes (+½, +½, +½, −½) with average ¼, so the three empty doors "
        "become 0 and the prize becomes 1. In arrow terms: on |11⟩ all four path arrows line "
        "up, on every other door they cancel in pairs. With N doors Grover's search needs "
        "about (π/4)√N oracle queries instead of about N/2."
    ),
    par_runs=3,
)

LEVELS: tuple[Level, ...] = (INVISIBLE_INK, DARK_PORT, ERASER, KICKBACK, AMPLIFIER)
LEVELS_BY_ID: dict[str, Level] = {lvl.id: lvl for lvl in LEVELS}

# Mystery phases for Dark Port: multiples of 15 deg, avoiding 0 and 180 (no sign puzzle).
MYSTERY_CHOICES: tuple[int, ...] = (30, 45, 60, 75, 90, 105, 120, 135, 150,
                                    210, 225, 240, 255, 270, 285, 300, 315, 330)


def get_level(level_id: str) -> Level:
    try:
        return LEVELS_BY_ID[level_id]
    except KeyError:
        raise ValueError(f"unknown level {level_id!r}; choose one of {list(LEVELS_BY_ID)}") from None


def mystery_phase(seed: int) -> int:
    """Hidden phase (degrees) for an attempt seed. Deterministic, so a solution can be
    re-checked on IonQ in a later Qollab Run with the same seed."""
    digest = hashlib.sha256(f"phase-shift/dark-port/{int(seed)}".encode()).digest()
    return MYSTERY_CHOICES[int.from_bytes(digest[:4], "big") % len(MYSTERY_CHOICES)]
