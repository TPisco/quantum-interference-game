"""JS-facing facade for the web UI (Qollab "JS + Qiskit" project).

The page imports this module statically (the form Qollab resolves)::

    import * as api from "phaseshift.api";
    const proxy = await api.run_level.callPromising(backend, "invisible-ink",
                                                    {phi: 180, recombine: true},
                                                    {where: "backend", shots: 1000});
    const result = proxy.toJs({dict_converter: Object.fromEntries});
    proxy.destroy();

``backend`` is the global object Qollab creates from the "Select QPU" dialog
(IonQ's simulator or the built-in simulator). This module never creates it.

Every function returns a plain dict ``{"ok": True, ...}`` or
``{"ok": False, "error": "...", "code": "..."}`` and never raises, so the UI
can always leave its "running" state.

Platform rules we design around (found by other hackathon teams and confirmed
by Qollab mentors): an IonQ job accepts ONE circuit, and each Qollab Run allows
ONE IonQ job. Practice runs therefore use an in-browser simulator
(``where="local"``), and the player spends the IonQ job on the solution they
want to confirm (``where="backend"``).
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable

from . import __version__
from . import circuits, execution, game, paths
from .levels import LEVELS, get_level

ATTRIBUTION = "This effort is supported by Qollab & IonQ."
DEFAULT_SHOTS = 1000
MIN_SHOTS, MAX_SHOTS = 50, 4000

# One IonQ job per backend object (Qollab creates a fresh backend on every Run).
_IONQ: dict[str, Any] = {"backend": None, "used": False}


class ApiError(ValueError):
    def __init__(self, message: str, code: str = "bad_input"):
        super().__init__(message)
        self.code = code


def _py(x: Any) -> Any:
    """Pyodide JsProxy -> Python (dicts, lists); plain Python passes through."""
    return x.to_py() if hasattr(x, "to_py") else x


def _missing(backend: Any) -> bool:
    return backend is None or type(backend).__name__ in ("JsNull", "JsUndefined")


def _plain(x: Any) -> Any:
    """Recursively convert to JSON-safe builtins (numpy scalars, tuples...)."""
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, int):
        return int(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)


def _safe(fn: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return _plain({"ok": True, **fn(*args, **kwargs)})
        except ApiError as exc:
            return {"ok": False, "error": str(exc), "code": exc.code}
        except (circuits.ConfigError, ValueError) as exc:
            return {"ok": False, "error": str(exc), "code": "bad_input"}
        except Exception as exc:  # noqa: BLE001 - the UI must never hang
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "code": "backend_error"}
    return wrapper


def _ionq_state(backend: Any) -> dict[str, Any]:
    if _IONQ["backend"] is not backend:
        _IONQ.update(backend=backend, used=False)
    return _IONQ


# --------------------------------------------------------------------------
# Static information
# --------------------------------------------------------------------------

@_safe
def info() -> dict[str, Any]:
    """Game description for the UI: levels (no hidden values), defaults, version."""
    return {"version": __version__, "attribution": ATTRIBUTION,
            "levels": [lvl.public() for lvl in LEVELS],
            "shots": {"default": DEFAULT_SHOTS, "min": MIN_SHOTS, "max": MAX_SHOTS}}


@_safe
def backend_info(backend: Any = None) -> dict[str, Any]:
    """What Qollab selected in "Select QPU" (no job is submitted)."""
    if _missing(backend):
        return {"available": False, "name": None, "is_ionq": False, "ionq_job_used": False}
    ionq = execution.is_ionq(backend)
    return {"available": True, "name": execution.backend_name(backend), "is_ionq": ionq,
            "ionq_job_used": bool(ionq and _ionq_state(backend)["used"])}


@_safe
def default_config(level_id: str) -> dict[str, Any]:
    """Reset helper: the level's starting configuration."""
    return {"config": get_level(str(level_id)).default_config()}


@_safe
def progress_status(progress: Any = None) -> dict[str, Any]:
    """Clean stored progress and list unlocked levels."""
    p = game.clean_progress(_py(progress))
    return {"progress": p, "unlocked": game.unlocked(p)}


@_safe
def preview(level_id: str, config: Any = None, seed: Any = 0) -> dict[str, Any]:
    """Circuit drawing and Qiskit code for a configuration, without running anything."""
    level = get_level(str(level_id))
    cfg = circuits.normalize_config(level, _py(config))
    return {"config": cfg, "circuit_text": circuits.circuit_text(level, cfg, seed=int(seed or 0)),
            "qiskit_code": circuits.qiskit_code(level, cfg)}


# --------------------------------------------------------------------------
# Running a level
# --------------------------------------------------------------------------

def _options(options: Any) -> dict[str, Any]:
    o = _py(options) or {}
    if not isinstance(o, dict):
        raise ApiError("options must be an object")
    where = str(o.get("where", "local"))
    if where not in ("local", "backend"):
        raise ApiError("where must be 'local' or 'backend'")
    try:
        shots = int(o.get("shots", DEFAULT_SHOTS))
        seed = int(o.get("seed", 0) or 0)
        runs_before = max(0, int(o.get("runs_before", 0) or 0))
    except (TypeError, ValueError):
        raise ApiError("shots, seed and runs_before must be integers") from None
    if not MIN_SHOTS <= shots <= MAX_SHOTS:
        raise ApiError(f"shots must be between {MIN_SHOTS} and {MAX_SHOTS}")
    sim_seed = o.get("sim_seed")
    return {"where": where, "shots": shots, "seed": seed, "runs_before": runs_before,
            "progress": o.get("progress"), "sim_seed": None if sim_seed is None else int(sim_seed)}


@_safe
def run_level(backend: Any = None, level_id: str = "invisible-ink", config: Any = None,
              options: Any = None) -> dict[str, Any]:
    """Build the player's circuit, run it, and judge it.

    options:
      where       "local" (in-browser Qiskit simulator, unlimited) or
                  "backend" (the Qollab-selected backend: IonQ = one job per Run)
      shots       50..4000 (default 1000)
      seed        attempt seed (chooses the hidden phase of Dark Port)
      runs_before runs already used in this attempt (for the par star)
      progress    stored progress dict; the updated one is returned
    """
    level = get_level(str(level_id))
    cfg = circuits.normalize_config(level, _py(config))
    opt = _options(options)
    qc = circuits.build_circuit(level, cfg, seed=opt["seed"])

    if opt["where"] == "local":
        target = execution.local_backend()
        where_name = "In-browser Qiskit simulator"
    else:
        if _missing(backend):
            raise ApiError("No backend selected. On Qollab press Run and choose a simulator "
                           "in 'Select QPU'.", "no_backend")
        target = backend
        where_name = execution.backend_name(backend)
    on_ionq = opt["where"] == "backend" and execution.is_ionq(target)

    t0 = time.time()
    if on_ionq:
        state = _ionq_state(target)
        if state["used"]:
            raise ApiError("IonQ allows one job per Qollab Run and this Run already used it. "
                           "Press Stop, then Run, to send another job. Practice runs on the "
                           "in-browser simulator are unlimited.", "ionq_job_used")
        job = execution.submit(target, qc, shots=opt["shots"])
        state["used"] = True  # accepted: the job for this Run is spent
        counts = execution.counts_from_job(job, qc.num_clbits)
    else:
        counts = execution.run_circuit(target, qc, shots=opt["shots"], seed=opt["sim_seed"])
    elapsed = time.time() - t0

    shots = sum(counts.values())
    probs = execution.to_probabilities(counts)
    theory = paths.analyze(circuits.build_circuit(level, cfg, seed=opt["seed"], measure=False),
                           level.outcome_names)
    runs = opt["runs_before"] + 1
    fb = game.evaluate(level, cfg, probs, runs=runs, on_ionq=on_ionq, seed=opt["seed"])
    progress = game.record(opt["progress"], level.id, fb.stars, on_ionq)

    # Dark Port: the arrows would reveal the hidden phase, so they stay hidden until solved.
    reveal = fb.solved or not any(s.gate == "mystery" for s in level.steps)
    outcomes = []
    for o in theory["outcomes"]:
        k = o["key"]
        lo, hi = execution.wilson_interval(counts[k], shots)
        item = {"key": k, "label": o["label"], "count": counts[k], "measured": probs[k],
                "ci": [lo, hi], "is_target": k in level.target.outcomes}
        if reveal:
            item.update(theory=o["theory"], classical=o["classical"],
                        interference=o["interference"], arrows=o["arrows"], sum=o["sum"])
        outcomes.append(item)

    marginals = []
    if level.num_qubits > 1:
        for q, name in enumerate(level.qubit_names):
            m = paths.marginal(probs, q, level.num_qubits)
            t = paths.marginal(theory["theory"], q, level.num_qubits)
            marginals.append({"qubit": q, "name": name, "measured": m, "theory": t})

    return {
        "level": level.id,
        "config": cfg,
        "source": {"where": opt["where"], "name": where_name, "is_ionq": on_ionq,
                   "seconds": round(elapsed, 3)},
        "shots": shots,
        "counts": counts,
        "probabilities": probs,
        "outcomes": outcomes,
        "marginals": marginals,
        "revealed": reveal,
        "target": {**level.target.public(), "value": fb.value},
        "feedback": fb.as_dict(),
        "learn": level.learn if fb.solved else None,
        "runs": runs,
        "progress": progress,
        "unlocked": game.unlocked(progress),
        "next_level": game.next_level(level.id) if fb.solved else None,
        "circuit_text": circuits.circuit_text(level, cfg, seed=opt["seed"]),
        "qiskit_code": circuits.qiskit_code(level, cfg),
    }
