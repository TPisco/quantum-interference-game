"""Exact theory for a circuit: path sums, a.k.a. "amplitude arrows".

Every way the qubits can travel from the start state to a measurement outcome
is a *path*. Each path carries a complex amplitude, which we draw as an arrow
(Feynman's picture from *QED*). For each outcome:

* quantum probability   = |sum of the arrows|^2   (add arrows, then square)
* classical probability = sum of |arrow|^2        (square each, then add: what
  you would get if the paths were told apart, or if H were a fair coin flip)
* interference term     = quantum - classical

If only one arrow lands on an outcome, quantum == classical and the phase is
invisible. Interference needs two or more arrows on the same outcome. That is
the whole game in one sentence.

The path enumeration multiplies gate matrix elements along computational-basis
paths, so it is exact and cheap for the small circuits used here (<= 16 paths).
"""

from __future__ import annotations

import cmath
from typing import Any

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

_EPS = 1e-12


def enumerate_paths(qc: QuantumCircuit) -> list[tuple[int, complex, list[int]]]:
    """All computational-basis paths through ``qc`` (measurements ignored).

    Returns ``(final_state, amplitude, history)`` where ``history`` lists the
    basis state (little-endian integer, Qiskit order) after every gate,
    starting with the initial |0...0>.
    """
    paths: list[tuple[int, complex, list[int]]] = [(0, complex(cmath.exp(1j * float(qc.global_phase))), [0])]
    for inst in qc.data:
        op = inst.operation
        if op.name in ("measure", "barrier", "delay"):
            continue
        qidx = [qc.find_bit(q).index for q in inst.qubits]
        mat = Operator(op).data
        k = len(qidx)
        new: list[tuple[int, complex, list[int]]] = []
        for state, amp, hist in paths:
            local_in = sum(((state >> q) & 1) << j for j, q in enumerate(qidx))
            for local_out in range(2**k):
                m = complex(mat[local_out, local_in])
                if abs(m) < _EPS:
                    continue
                s = state
                for j, q in enumerate(qidx):
                    s = (s & ~(1 << q)) | (((local_out >> j) & 1) << q)
                new.append((s, amp * m, hist + [s]))
        paths = new
    return paths


def _c(z: complex) -> dict[str, float]:
    return {"re": round(z.real, 12), "im": round(z.imag, 12)}


def analyze(qc: QuantumCircuit, outcome_labels: dict[str, str] | None = None) -> dict[str, Any]:
    """Arrows, classical and quantum probabilities for every outcome of ``qc``.

    ``qc`` must not contain measurements of a subset only; measurements are ignored.
    The result is JSON-safe.
    """
    n = qc.num_qubits
    keys = [format(i, f"0{n}b") for i in range(2**n)]
    groups: dict[str, list[tuple[complex, list[int]]]] = {k: [] for k in keys}
    for state, amp, hist in enumerate_paths(qc):
        groups[format(state, f"0{n}b")].append((amp, hist))

    bare = qc.remove_final_measurements(inplace=False)
    exact = Statevector(bare).probabilities_dict()

    outcomes = []
    for key in keys:
        arrows = groups[key]
        total = sum((a for a, _ in arrows), 0j)
        quantum = abs(total) ** 2
        classical = sum(abs(a) ** 2 for a, _ in arrows)
        outcomes.append({
            "key": key,
            "label": (outcome_labels or {}).get(key, f"|{key}⟩"),
            "theory": round(quantum, 12),
            "classical": round(classical, 12),
            "interference": round(quantum - classical, 12),
            "arrows": [
                {**_c(a), "arm": "upper" if (len(h) > 1 and (h[1] & 1) == 0) else "lower",
                 "history": [format(s, f"0{n}b") for s in h]}
                for a, h in arrows
            ],
            "sum": _c(total),
        })
        # The path sum must agree with Qiskit's statevector (guards against bugs).
        assert abs(quantum - exact.get(key, 0.0)) < 1e-9, (key, quantum, exact.get(key))
    return {"outcomes": outcomes, "theory": {o["key"]: o["theory"] for o in outcomes}}


def marginal(probabilities: dict[str, float], qubit: int, n: int) -> dict[str, float]:
    """P(qubit = 0) and P(qubit = 1) from a joint distribution with Qiskit keys."""
    p1 = sum(p for k, p in probabilities.items() if k.zfill(n)[n - 1 - qubit] == "1")
    return {"0": 1.0 - p1, "1": p1}
