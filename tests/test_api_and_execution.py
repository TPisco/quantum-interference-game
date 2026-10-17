"""The JS-facing API, backends, IonQ compatibility and progression."""

import warnings

import pytest
from qiskit import QuantumCircuit

from phaseshift import api, circuits, execution, game
from phaseshift.levels import LEVELS, get_level, mystery_phase


# --------------------------------------------------------------------------
# Fake backends
# --------------------------------------------------------------------------

class _Result:
    def __init__(self, counts):
        self._counts = counts

    def get_counts(self):
        return self._counts


class _Job:
    def __init__(self, counts):
        self._counts = counts

    def result(self):
        return _Result(self._counts)


class FakeIonQ:
    """Looks like an IonQ backend by name; returns ideal counts from the local simulator."""

    name = "ionq_simulator"

    def __init__(self):
        self.jobs = []

    def run(self, qc, shots=1000, **kwargs):
        self.jobs.append(qc)
        allowed = set(execution.IONQ_BASIS) | {"measure"}
        assert set(qc.count_ops()) <= allowed, qc.count_ops()
        return _Job(execution.run_circuit(execution.local_backend(), qc, shots=shots, seed=1))


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

def test_info_lists_levels_without_secrets():
    info = api.info()
    assert info["ok"]
    assert [lvl["id"] for lvl in info["levels"]] == [lvl.id for lvl in LEVELS]
    text = str(info)
    assert "theta" not in text.lower() or "θ" in text  # never a numeric hidden phase
    assert info["attribution"] == "This effort is supported by Qollab & IonQ."


def test_run_level_local_solution():
    r = api.run_level(None, "invisible-ink", {"phi": 180, "recombine": True},
                      {"where": "local", "sim_seed": 3})
    assert r["ok"], r
    assert r["probabilities"]["1"] == pytest.approx(1.0)
    assert r["feedback"]["solved"] and r["feedback"]["stars"] == 2
    assert r["unlocked"] == ["invisible-ink", "dark-port"]
    assert r["next_level"] == "dark-port"
    assert r["source"]["where"] == "local" and not r["source"]["is_ionq"]
    assert sum(o["measured"] for o in r["outcomes"]) == pytest.approx(1.0)
    assert "qc.h(0)" in r["qiskit_code"]


def test_run_level_feedback_close_and_invisible():
    r = api.run_level(None, "invisible-ink", {"phi": 90, "recombine": False}, {"where": "local"})
    assert r["feedback"]["headline"] == "The phase is invisible!"
    r = api.run_level(None, "invisible-ink", {"phi": 135, "recombine": True},
                      {"where": "local", "sim_seed": 2})
    assert r["feedback"]["headline"] == "You're close."
    assert "Try adjusting the phase gate" in r["feedback"]["detail"]


def test_dark_port_hides_arrows_until_solved():
    seed = 11
    theta = mystery_phase(seed)
    r = api.run_level(None, "dark-port", {"phi": (theta + 90) % 360}, {"where": "local", "seed": seed})
    assert r["ok"] and not r["revealed"]
    assert all("arrows" not in o and "theory" not in o for o in r["outcomes"])
    assert str(theta) + "°" not in r["feedback"]["detail"]
    r = api.run_level(None, "dark-port", {"phi": (360 - theta) % 360},
                      {"where": "local", "seed": seed, "runs_before": 1})
    assert r["feedback"]["solved"] and r["revealed"]
    assert all("arrows" in o for o in r["outcomes"])
    assert "θ ?" in r["circuit_text"]  # the drawing never shows the hidden value


def test_eraser_marginals():
    r = api.run_level(None, "eraser", {"phi": 180, "eraser": True}, {"where": "local", "sim_seed": 4})
    assert r["feedback"]["solved"]
    assert [m["name"] for m in r["marginals"]] == ["photon", "detector"]
    assert r["marginals"][0]["theory"]["1"] == pytest.approx(0.5)


def test_bad_inputs_return_errors_not_exceptions():
    assert api.run_level(None, "nope", {}, {})["code"] == "bad_input"
    assert api.run_level(None, "eraser", {"bogus": 1}, {})["code"] == "bad_input"
    assert api.run_level(None, "eraser", {}, {"where": "moon"})["code"] == "bad_input"
    assert api.run_level(None, "eraser", {}, {"shots": 10})["code"] == "bad_input"
    assert api.run_level(None, "eraser", {}, {"where": "backend"})["code"] == "no_backend"


def test_ionq_one_job_per_run_guard():
    backend = FakeIonQ()
    info = api.backend_info(backend)
    assert info["is_ionq"] and not info["ionq_job_used"]
    r = api.run_level(backend, "invisible-ink", {"phi": 180, "recombine": True},
                      {"where": "backend", "runs_before": 9})
    assert r["ok"], r
    assert r["source"]["is_ionq"] and r["feedback"]["stars"] == 2  # solved + IonQ (over par)
    assert r["progress"]["ionq"] == ["invisible-ink"]
    assert len(backend.jobs) == 1 and backend.jobs[0].num_qubits == 1
    again = api.run_level(backend, "invisible-ink", {"phi": 0}, {"where": "backend"})
    assert again["code"] == "ionq_job_used" and len(backend.jobs) == 1
    assert api.backend_info(backend)["ionq_job_used"]
    # Local practice keeps working, and a new Run (new backend object) gets a new job.
    assert api.run_level(backend, "invisible-ink", {}, {"where": "local"})["ok"]
    assert api.run_level(FakeIonQ(), "invisible-ink", {}, {"where": "backend"})["ok"]


def test_non_ionq_backend_unlimited():
    backend = execution.local_backend()
    for _ in range(3):
        r = api.run_level(backend, "eraser", {"phi": 180, "eraser": True}, {"where": "backend"})
        assert r["ok"] and not r["source"]["is_ionq"]
        assert r["feedback"]["stars"] == 2


def test_preview_and_default_config():
    assert api.default_config("eraser")["config"] == {"phi": 0.0, "eraser": False}
    p = api.preview("invisible-ink", {"phi": 45, "recombine": True})
    assert p["ok"] and "P(π/4)" in p["circuit_text"]


# --------------------------------------------------------------------------
# Execution helpers
# --------------------------------------------------------------------------

def test_normalize_counts_and_probabilities():
    assert execution.normalize_counts({"0x1": 3, "0": 1}, 2) == {"00": 1, "01": 3, "10": 0, "11": 0}
    assert execution.normalize_counts({"1 0": 5}, 2) == {"00": 0, "01": 0, "10": 5, "11": 0}
    assert execution.to_probabilities({"0": 720, "1": 280}) == {"0": 0.72, "1": 0.28}
    lo, hi = execution.wilson_interval(500, 1000)
    assert lo < 0.5 < hi and hi - lo < 0.07


def test_wide_backend_circuits_are_trimmed():
    from qiskit.providers.fake_provider import GenericBackendV2

    wide = GenericBackendV2(num_qubits=20, seed=1)
    qc = circuits.build_circuit(get_level("eraser"), {"phi": 90, "eraser": True})
    compiled = execution.compile_for(wide, qc)
    assert compiled.num_qubits == 2


@pytest.mark.parametrize("level", LEVELS, ids=lambda lvl: lvl.id)
def test_circuits_serialize_for_ionq_offline(level):
    """qiskit-ionq can turn every compiled level circuit into an IonQ job payload."""
    from qiskit_ionq import IonQProvider
    from qiskit_ionq.helpers import qiskit_to_ionq

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        backend = IonQProvider("offline-test-token").get_backend("simulator")
        toggles = {c.id: True for c in level.controls if c.kind == "toggle"}
        qc = circuits.build_circuit(level, {"phi": 135, **toggles}, seed=3)
        compiled = execution.compile_for(backend, qc)
        payload = qiskit_to_ionq(compiled, backend)
    assert '"circuit"' in payload or "circuit" in payload
    assert set(compiled.count_ops()) <= set(execution.IONQ_BASIS) | {"measure"}


@pytest.mark.parametrize("level", LEVELS, ids=lambda lvl: lvl.id)
@pytest.mark.parametrize("toggles_on", [False, True])
def test_qiskit_code_runs_and_matches_circuit(level, toggles_on):
    """The code shown to players is real Qiskit that builds the same unitary."""
    from qiskit.quantum_info import Operator

    seed = 11
    cfg = {"phi": 105, **{c.id: toggles_on for c in level.controls if c.kind == "toggle"}}
    ns = {"theta": mystery_phase(seed)}
    exec(circuits.qiskit_code(level, cfg), ns)  # noqa: S102 - our own generated code
    shown: QuantumCircuit = ns["qc"].remove_final_measurements(inplace=False)
    built = circuits.build_circuit(level, cfg, seed=seed, measure=False)
    assert Operator(shown).equiv(Operator(built))


def test_marginals_only_where_they_teach_something():
    r = api.run_level(None, "kickback", {"phi": 180, "flip": True}, {"where": "local", "sim_seed": 2})
    assert r["ok"] and r["feedback"]["solved"]
    target = next(m for m in r["marginals"] if m["name"] == "target")
    assert target["measured"]["1"] == pytest.approx(1.0)
    assert "never" in r["marginal_note"]
    r = api.run_level(None, "amplifier", {"phi": 180, "diffuser": True}, {"where": "local"})
    assert r["ok"] and r["marginals"] == [] and r["marginal_note"] is None


# --------------------------------------------------------------------------
# Progression
# --------------------------------------------------------------------------

def test_progression_unlocks_in_order_and_keeps_best():
    p = game.new_progress()
    assert game.unlocked(p) == ["invisible-ink"]
    p = game.record(p, "invisible-ink", 1, on_ionq=False)
    assert game.unlocked(p) == ["invisible-ink", "dark-port"]
    p = game.record(p, "invisible-ink", 3, on_ionq=True)
    p = game.record(p, "invisible-ink", 2, on_ionq=False)
    assert p["stars"]["invisible-ink"] == 3 and p["ionq"] == ["invisible-ink"]
    p = game.record(p, "dark-port", 2, on_ionq=False)
    assert game.unlocked(p) == ["invisible-ink", "dark-port", "eraser"]
    for lvl in LEVELS[2:-1]:
        p = game.record(p, lvl.id, 1, on_ionq=False)
    assert game.unlocked(p) == [lvl.id for lvl in LEVELS]
    assert game.clean_progress({"stars": {"x": 5, "eraser": "9"}, "ionq": ["zz"]}) == {
        "stars": {"eraser": 3}, "ionq": []}
    assert game.clean_progress("garbage") == game.new_progress()


@pytest.mark.parametrize("name,expected", [
    ("ionq_simulator", True), ("qpu.forte-1", True), ("simulator.aria-1", True),
    ("IonQ Forte 1 (Remote simulator)", True), ("basic_simulator", False),
    ("aer_simulator", False), ("variational_sim", False), ("generic_backend_5q", False),
])
def test_is_ionq_by_name(name, expected):
    backend = type("B", (), {"name": name})()
    assert execution.is_ionq(backend) is expected


# --------------------------------------------------------------------------
# Interference curve (api.sweep)
# --------------------------------------------------------------------------

def test_sweep_matches_known_formulas():
    import math

    r = api.sweep("invisible-ink", {"phi": 90, "recombine": True}, 0, False)
    assert r["ok"] and not r["hidden"] and not r["flat"]
    assert len(r["points"]) == 73 and r["points"][0]["phi"] == 0 and r["points"][-1]["phi"] == 360
    for p in r["points"]:
        assert p["value"] == pytest.approx(math.sin(math.radians(p["phi"]) / 2) ** 2, abs=1e-6)
    assert r["current"] == {"phi": 90.0, "value": pytest.approx(0.5, abs=1e-6)}
    assert r["best"]["phi"] == 180 and r["best"]["value"] == pytest.approx(1.0)

    amp = api.sweep("amplifier", {"phi": 0, "diffuser": True}, 0, False)
    for p in amp["points"]:
        assert p["value"] == pytest.approx((10 - 6 * math.cos(math.radians(p["phi"]))) / 16, abs=1e-6)


def test_sweep_is_flat_without_interference():
    r = api.sweep("invisible-ink", {"phi": 0, "recombine": False}, 0, False)
    assert r["ok"] and r["flat"]
    assert all(p["value"] == pytest.approx(0.5) for p in r["points"])


def test_sweep_hides_the_mystery_phase_until_revealed():
    hidden = api.sweep("dark-port", {"phi": 0}, 7, False)
    assert hidden == {"ok": True, "level": "dark-port", "hidden": True}
    shown = api.sweep("dark-port", {"phi": 0}, 7, True)
    assert shown["ok"] and not shown["hidden"]
    # The darkest phase cancels the hidden one: phi = -theta (mod 360).
    assert shown["best"]["phi"] == (-mystery_phase(7)) % 360
    assert shown["best"]["value"] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("level", LEVELS, ids=lambda lvl: lvl.id)
def test_sweep_works_on_every_level(level):
    r = api.sweep(level.id, level.default_config(), 1, True)
    assert r["ok"], r
    assert all(0.0 <= p["value"] <= 1.0 for p in r["points"])


def test_sweep_bad_level_is_an_error_not_an_exception():
    r = api.sweep("no-such-level", {}, 0, True)
    assert r["ok"] is False and r["code"] == "bad_input"
