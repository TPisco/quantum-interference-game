"""Run circuits on simulators and turn counts into probabilities.

Three ways to get a backend:

* ``local_backend()``  - Qiskit's ``BasicSimulator`` (pure Python). It works
  everywhere, including in the browser on Qollab (Pyodide), so the game can
  give instant, unlimited practice runs.
* On Qollab the platform creates a ``backend`` object from the "Select QPU"
  dialog (IonQ's simulator or Qollab's built-in simulator) and the web UI hands
  it to ``phaseshift.api``. Nothing here creates or configures it.
* ``ionq_backend()``   - for local development outside Qollab: IonQ's cloud
  simulator through ``qiskit-ionq``. Needs ``IONQ_API_KEY`` in the environment.

``run_circuit`` compiles for the given backend and returns plain counts.
``to_probabilities`` normalises counts to ``{"0": 0.72, "1": 0.28}``.
"""

from __future__ import annotations

import math
import os
import re
from typing import Any

from qiskit import QuantumCircuit, transpile

# Gates IonQ's API accepts directly (Qiskit names). P(phi) becomes RZ(phi).
IONQ_BASIS = ["h", "x", "y", "z", "s", "sdg", "rx", "ry", "rz", "cx"]
_NON_GATES = {"measure", "reset", "delay", "barrier", "if_else", "while_loop",
              "for_loop", "switch_case", "break_loop", "continue_loop"}


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

def local_backend() -> Any:
    """Qiskit's pure-Python simulator (no network, no compiled extensions)."""
    from qiskit.providers.basic_provider import BasicSimulator

    return BasicSimulator()


def aer_backend() -> Any:
    """Qiskit Aer, if installed (faster locally; not available in the browser)."""
    from qiskit_aer import AerSimulator

    return AerSimulator()


def ionq_backend(noise_model: str | None = None, token: str | None = None) -> Any:
    """IonQ's cloud simulator via ``qiskit-ionq`` (local development only).

    ``noise_model``: ``None``/``"ideal"`` or a hardware model such as ``"aria-1"``
    or ``"forte-1"``. The API key is read from ``IONQ_API_KEY`` unless given.
    On Qollab you do not call this: the platform injects the IonQ backend.
    """
    from qiskit_ionq import IonQProvider

    token = token or os.environ.get("IONQ_API_KEY") or os.environ.get("IONQ_API_TOKEN")
    if not token:
        raise RuntimeError("Set IONQ_API_KEY to use IonQ's simulator outside Qollab.")
    backend = IonQProvider(token).get_backend("simulator")
    if noise_model and noise_model != "ideal":
        backend.set_options(noise_model=noise_model)
    return backend


def get_backend(kind: str = "local", **kwargs: Any) -> Any:
    """``"local"`` (BasicSimulator), ``"aer"`` or ``"ionq"``."""
    kind = kind.lower()
    if kind in ("local", "basic", "basic_simulator"):
        return local_backend()
    if kind == "aer":
        return aer_backend()
    if kind == "ionq":
        return ionq_backend(**kwargs)
    raise ValueError(f"unknown backend kind {kind!r} (use local, aer or ionq)")


def backend_name(backend: Any) -> str:
    """Name for BackendV1 (method) and BackendV2 (attribute) alike."""
    name = getattr(backend, "name", None)
    if callable(name):
        try:
            name = name()
        except Exception:  # noqa: BLE001
            name = None
    return str(name) if name else type(backend).__name__


_IONQ_NAME = re.compile(r"ionq|forte|harmony|tempo|(?<![a-z])aria(?![a-z])")


def is_ionq(backend: Any) -> bool:
    """True for IonQ backends: qiskit-ionq classes, or an IonQ system/simulator name
    (for example ``ionq_simulator``, ``qpu.forte-1`` or ``simulator.aria-1``)."""
    if type(backend).__module__.startswith("qiskit_ionq"):
        return True
    names = [backend_name(backend).lower(), type(backend).__name__.lower()]
    provider = getattr(backend, "provider", None)
    if provider is not None and not callable(provider):
        names.append(type(provider).__name__.lower())
    return any(_IONQ_NAME.search(n) for n in names)


# --------------------------------------------------------------------------
# Compilation
# --------------------------------------------------------------------------

def _drop_idle_qubits(qc: QuantumCircuit, n: int) -> QuantumCircuit:
    """Keep only qubits 0..n-1 if the others are idle (wide simulators are slow)."""
    if qc.num_qubits <= n:
        return qc
    if any(qc.find_bit(q).index >= n for inst in qc.data for q in inst.qubits):
        return qc
    out = QuantumCircuit(n, name=qc.name, global_phase=qc.global_phase)
    for creg in qc.cregs:
        out.add_register(creg)
    for inst in qc.data:
        out.append(inst.operation, [qc.find_bit(q).index for q in inst.qubits], list(inst.clbits))
    return out


def compile_for(backend: Any, qc: QuantumCircuit) -> QuantumCircuit:
    """Translate ``qc`` for ``backend`` without re-optimising the player's circuit.

    optimization_level=0 keeps every gate the player chose (so IonQ really runs
    H - P - H, not a simplified X). Only the gate names are translated.
    """
    if is_ionq(backend):
        try:
            return transpile(qc, basis_gates=IONQ_BASIS, optimization_level=0)
        except Exception:  # noqa: BLE001 - IonQ also accepts the logical circuit
            return qc
    n = qc.num_qubits
    try:
        compiled = transpile(qc, backend=backend, optimization_level=0,
                             initial_layout=list(range(n)))
        return _drop_idle_qubits(compiled, n)
    except Exception:  # noqa: BLE001 - backend without a usable target
        names = getattr(backend, "operation_names", None)
        basis = [g for g in (names or IONQ_BASIS) if g not in _NON_GATES]
        return transpile(qc, basis_gates=basis, optimization_level=0)


# --------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------

def submit(backend: Any, qc: QuantumCircuit, shots: int = 1000, seed: int | None = None) -> Any:
    """Compile and submit ONE circuit; return the job.

    Qollab's IonQ service accepts a single circuit per job, so we never batch.
    """
    compiled = compile_for(backend, qc)
    options: dict[str, Any] = {"shots": int(shots)}
    if seed is not None and not is_ionq(backend):
        options["seed_simulator"] = int(seed)
    try:
        return backend.run(compiled, **options)
    except TypeError:
        # Some backends reject seed_simulator; retry with shots only.
        return backend.run(compiled, shots=int(shots))


def normalize_counts(counts: dict[str, Any], num_clbits: int) -> dict[str, int]:
    """Counts with every outcome present, keys as plain ``num_clbits``-bit strings.

    Handles hex keys (``"0x1"``) and keys with spaces (multiple registers).
    """
    out = {format(i, f"0{num_clbits}b"): 0 for i in range(2**num_clbits)}
    for key, value in dict(counts).items():
        k = str(key).replace(" ", "")
        if k.startswith("0x"):
            k = format(int(k, 16), f"0{num_clbits}b")
        k = k.zfill(num_clbits)[-num_clbits:]
        out[k] = out.get(k, 0) + int(round(float(value)))
    return out


def counts_from_job(job: Any, num_clbits: int) -> dict[str, int]:
    result = job.result()
    return normalize_counts(result.get_counts(), num_clbits)


def run_circuit(backend: Any, qc: QuantumCircuit, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
    """Run one circuit and return complete counts, e.g. ``{"0": 274, "1": 726}``."""
    return counts_from_job(submit(backend, qc, shots=shots, seed=seed), qc.num_clbits)


def to_probabilities(counts: dict[str, int]) -> dict[str, float]:
    """``{"0": 720, "1": 280}`` -> ``{"0": 0.72, "1": 0.28}``."""
    total = sum(counts.values())
    if total <= 0:
        return {k: 0.0 for k in counts}
    return {k: v / total for k, v in counts.items()}


def wilson_interval(successes: float, shots: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a measured probability (honest error bars)."""
    if shots <= 0:
        return (0.0, 1.0)
    p = successes / shots
    denom = 1 + z * z / shots
    centre = (p + z * z / (2 * shots)) / denom
    half = z * math.sqrt(p * (1 - p) / shots + z * z / (4 * shots * shots)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
