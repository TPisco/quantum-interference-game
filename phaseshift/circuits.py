"""Build Qiskit circuits from a level and the player's configuration.

>>> from phaseshift.levels import get_level
>>> qc = build_circuit(get_level("invisible-ink"), {"phi": 180, "recombine": True})
>>> qc.count_ops()["h"]
2

The same function feeds every backend (local simulator, Qollab's built-in
simulator, IonQ), so what the player sees in the UI is exactly what runs.
"""

from __future__ import annotations

import math
from typing import Any

from qiskit import QuantumCircuit
from qiskit.circuit import Gate

from .levels import Level, mystery_phase


class ConfigError(ValueError):
    """The player configuration is invalid (message is safe to show in the UI)."""


def normalize_config(level: Level, config: dict[str, Any] | None) -> dict[str, Any]:
    """Validate ``config`` against the level's controls; fill defaults; snap angles.

    Unknown keys are rejected so typos do not silently use a default.
    """
    config = dict(config or {})
    unknown = set(config) - {c.id for c in level.controls}
    if unknown:
        raise ConfigError(f"unknown control(s) for {level.id}: {sorted(unknown)}")
    out: dict[str, Any] = {}
    for c in level.controls:
        v = config.get(c.id, c.default)
        if c.kind == "angle":
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise ConfigError(f"{c.label} must be a number of degrees") from None
            if not math.isfinite(v):
                raise ConfigError(f"{c.label} must be finite")
            v = v % 360.0
            if c.step:
                v = (round(v / c.step) * c.step) % 360.0
            out[c.id] = v
        elif c.kind == "toggle":
            if isinstance(v, str):
                v = v.strip().lower() in ("1", "true", "on", "yes")
            out[c.id] = bool(v)
        else:  # pragma: no cover - guarded by level definitions
            raise ConfigError(f"unsupported control kind {c.kind}")
    return out


def diffuser_gate() -> Gate:
    """Grover's diffuser on two qubits, 2|s><s| - I, as one labelled gate.

    H H, then Z Z and CZ (together diag(1, -1, -1, -1) = 2|00><00| - I), then H H.
    Kept as a single instruction so the path sum treats it as one step (four
    arrows per door instead of sixteen); transpilation unrolls it for backends.
    """
    sub = QuantumCircuit(2, name="diffuser")
    sub.h([0, 1])
    sub.z([0, 1])
    sub.cz(0, 1)
    sub.h([0, 1])
    return sub.to_gate(label="Diffuser")


def _angle_of(step, config: dict[str, Any], seed: int) -> float:
    if step.gate == "mystery":
        return float(mystery_phase(seed))
    if step.angle:
        return float(config[step.angle])
    return float(step.fixed_angle or 0.0)


def build_circuit(
    level: Level,
    config: dict[str, Any] | None = None,
    *,
    seed: int = 0,
    measure: bool = True,
    hide_mystery: bool = False,
) -> QuantumCircuit:
    """Return the level's circuit for this configuration.

    seed:          attempt seed (picks the hidden phase in Dark Port).
    measure:       append measurements of every qubit (needed for any backend run).
    hide_mystery:  draw the hidden phase as an opaque "θ ?" box (for display only;
                   such a circuit cannot be simulated).
    """
    cfg = normalize_config(level, config)
    n = level.num_qubits
    qc = QuantumCircuit(n, n, name=level.id.replace("-", "_")) if measure else QuantumCircuit(
        n, name=level.id.replace("-", "_"))
    for step in level.steps:
        if step.toggle and not cfg[step.toggle]:
            continue
        if step.gate == "h":
            for q in step.qubits:
                qc.h(q)
        elif step.gate == "x":
            qc.x(step.qubits[0])
        elif step.gate == "cx":
            qc.cx(step.qubits[0], step.qubits[1])
        elif step.gate == "cp":
            qc.cp(math.radians(_angle_of(step, cfg, seed)), step.qubits[0], step.qubits[1])
        elif step.gate == "diffuser":
            qc.append(diffuser_gate(), [step.qubits[0], step.qubits[1]])
        elif step.gate in ("p", "mystery"):
            if step.gate == "mystery" and hide_mystery:
                qc.append(Gate("mystery", 1, [], label="θ ?"), [step.qubits[0]])
            else:
                qc.p(math.radians(_angle_of(step, cfg, seed)), step.qubits[0])
        else:  # pragma: no cover - guarded by level definitions
            raise ConfigError(f"unsupported gate {step.gate}")
    if measure:
        qc.measure(range(n), range(n))
    return qc


def angle_text(deg: float) -> str:
    """Pretty angle: ``180`` -> ``"180° (π)"``, ``45`` -> ``"45° (π/4)"``."""
    deg = float(deg) % 360.0
    from fractions import Fraction

    frac = Fraction(deg / 180.0).limit_denominator(24)
    if frac == 0:
        return "0°"
    if frac == 1:
        pi_txt = "π"
    elif frac.denominator == 1:
        pi_txt = f"{frac.numerator}π"
    elif frac.numerator == 1:
        pi_txt = f"π/{frac.denominator}"
    else:
        pi_txt = f"{frac.numerator}π/{frac.denominator}"
    return f"{deg:g}° ({pi_txt})"


def _code_lines(step, cfg: dict[str, Any]) -> list[str]:
    """Qiskit source lines for one step (the first line carries the comment)."""
    q = step.qubits
    if step.gate == "h":
        target = str(q[0]) if len(q) == 1 else str(list(q))
        return [f"qc.h({target})  # {step.label}"]
    if step.gate == "x":
        return [f"qc.x({q[0]})  # {step.label}"]
    if step.gate == "cx":
        return [f"qc.cx({q[0]}, {q[1]})  # {step.label}"]
    if step.gate == "mystery":
        return [f"qc.p(radians(theta), {q[0]})  # mystery sample (hidden)"]
    if step.gate == "p":
        return [f"qc.p(radians({cfg[step.angle]:g}), {q[0]})  # your phase φ"]
    if step.gate == "cp":
        return [f"qc.cp(radians({cfg[step.angle]:g}), {q[0]}, {q[1]})  # {step.label}"]
    if step.gate == "diffuser":
        pair = f"[{q[0]}, {q[1]}]"
        return [f"qc.h({pair})  # {step.label}: H H, Z Z, CZ, H H",
                f"qc.z({pair})", f"qc.cz({q[0]}, {q[1]})", f"qc.h({pair})"]
    raise ConfigError(f"unsupported gate {step.gate}")  # pragma: no cover


def qiskit_code(level: Level, config: dict[str, Any] | None = None) -> str:
    """Readable Qiskit source for the player's circuit (shown in the UI).

    The hidden phase of Dark Port is written as ``theta`` so it is not revealed.
    Switched-off gates are shown commented out.
    """
    cfg = normalize_config(level, config)
    n = level.num_qubits
    lines = ["from math import radians", "from qiskit import QuantumCircuit", "",
             f"qc = QuantumCircuit({n}, {n})"]
    for step in level.steps:
        body = _code_lines(step, cfg)
        if step.toggle and not cfg[step.toggle]:
            body = [f"# {body[0].split('  #')[0]}  # {step.label}: off"] + [f"# {x}" for x in body[1:]]
        lines.extend(body)
    lines.append(f"qc.measure({list(range(n))}, {list(range(n))})")
    return "\n".join(lines)


def circuit_text(level: Level, config: dict[str, Any] | None = None, *, seed: int = 0) -> str:
    """ASCII drawing of the circuit (hidden phase drawn as "θ ?")."""
    qc = build_circuit(level, config, seed=seed, hide_mystery=True)
    return str(qc.draw(output="text", fold=-1))
