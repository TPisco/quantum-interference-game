"""The quantum content of every level: formulas, path sums and solvability."""

import math

import pytest

from phaseshift import circuits, game, paths
from phaseshift.levels import LEVELS, MYSTERY_CHOICES, get_level, mystery_phase

ANGLES = [15.0 * k for k in range(24)]


def theory(level_id, config, seed=0):
    level = get_level(level_id)
    qc = circuits.build_circuit(level, config, seed=seed, measure=False)
    return paths.analyze(qc, level.outcome_names)


def sin2(deg):
    return math.sin(math.radians(deg) / 2) ** 2


@pytest.mark.parametrize("phi", ANGLES)
def test_invisible_ink_phase_alone_is_invisible(phi):
    t = theory("invisible-ink", {"phi": phi, "recombine": False})
    assert t["theory"]["1"] == pytest.approx(0.5)
    for o in t["outcomes"]:
        assert len(o["arrows"]) == 1  # one path per outcome: nothing to interfere with
        assert o["interference"] == pytest.approx(0.0)


@pytest.mark.parametrize("phi", ANGLES)
def test_invisible_ink_recombined_follows_sin2(phi):
    t = theory("invisible-ink", {"phi": phi, "recombine": True})
    assert t["theory"]["1"] == pytest.approx(sin2(phi), abs=1e-9)
    for o in t["outcomes"]:
        assert len(o["arrows"]) == 2
        assert o["classical"] == pytest.approx(0.5)  # classical coins would always give 50/50


@pytest.mark.parametrize("seed", range(40))
def test_dark_port_formula(seed):
    theta = mystery_phase(seed)
    assert theta in MYSTERY_CHOICES
    for phi in (0.0, 90.0, 225.0):
        t = theory("dark-port", {"phi": phi}, seed=seed)
        assert t["theory"]["1"] == pytest.approx(sin2(theta + phi), abs=1e-9)


@pytest.mark.parametrize("phi", ANGLES)
def test_eraser(phi):
    off = theory("eraser", {"phi": phi, "eraser": False})["theory"]
    on = theory("eraser", {"phi": phi, "eraser": True})["theory"]
    assert off["01"] + off["10"] == pytest.approx(0.5)
    assert all(v == pytest.approx(0.25) for v in off.values())
    assert on["01"] + on["10"] == pytest.approx(sin2(phi), abs=1e-9)
    # The photon on its own never shows fringes: the pattern lives in the correlation.
    assert paths.marginal(on, 0, 2)["1"] == pytest.approx(0.5)


@pytest.mark.parametrize("phi", ANGLES)
def test_kickback(phi):
    off = theory("kickback", {"phi": phi, "flip": False})["theory"]
    on = theory("kickback", {"phi": phi, "flip": True})["theory"]
    # Target in |0>: the controlled phase does nothing and H.H = I on the control.
    assert off["00"] == pytest.approx(1.0)
    # Target in |1>: the phase is kicked back onto the control...
    assert on["01"] + on["11"] == pytest.approx(sin2(phi), abs=1e-9)
    # ...and the target itself is never changed.
    assert paths.marginal(on, 1, 2)["1"] == pytest.approx(1.0)


@pytest.mark.parametrize("phi", ANGLES)
def test_amplifier(phi):
    off = theory("amplifier", {"phi": phi, "diffuser": False})
    on = theory("amplifier", {"phi": phi, "diffuser": True})
    assert all(v == pytest.approx(0.25) for v in off["theory"].values())
    expected = (10 - 6 * math.cos(math.radians(phi))) / 16
    assert on["theory"]["11"] == pytest.approx(expected, abs=1e-9)
    for o in on["outcomes"]:
        assert len(o["arrows"]) == 4  # every door is reached from all four doors
        assert o["classical"] == pytest.approx(0.25)


def test_amplifier_one_query_is_exact():
    on = theory("amplifier", {"phi": 180, "diffuser": True})
    assert on["theory"]["11"] == pytest.approx(1.0)
    eleven = next(o for o in on["outcomes"] if o["key"] == "11")
    # All four arrows point the same way (constructive), each of length 1/4.
    assert all(a["re"] == pytest.approx(0.25) and a["im"] == pytest.approx(0.0) for a in eleven["arrows"])


def test_mystery_seed_is_deterministic_and_varied():
    assert mystery_phase(123) == mystery_phase(123)
    assert len({mystery_phase(s) for s in range(200)}) > 10


@pytest.mark.parametrize("level", LEVELS, ids=lambda lvl: lvl.id)
def test_every_level_is_solvable_on_the_slider_grid(level):
    """Some configuration on the 15-degree grid meets the target with ideal probabilities,
    and the default configuration does not (the player has to do something)."""
    seed = 5
    toggles = [c.id for c in level.controls if c.kind == "toggle"]
    solved_somewhere = False
    for phi in ANGLES:
        for bits in range(2 ** len(toggles)):
            cfg = {"phi": phi, **{t: bool((bits >> i) & 1) for i, t in enumerate(toggles)}}
            probs = theory(level.id, cfg, seed)["theory"]
            fb = game.evaluate(level, circuits.normalize_config(level, cfg), probs, seed=seed)
            solved_somewhere |= fb.solved
    assert solved_somewhere
    default = level.default_config()
    probs = theory(level.id, default, seed)["theory"]
    assert not game.evaluate(level, circuits.normalize_config(level, default), probs, seed=seed).solved


@pytest.mark.parametrize("level_id", ["invisible-ink", "eraser", "amplifier"])
def test_toggles_off_mean_no_interference(level_id):
    """Without its 'interference enabling' toggle no outcome has two arrows (L1, L3, L5).
    (Kickback's toggle is different: without it the phase is absent, see test_kickback.)"""
    level = get_level(level_id)
    toggles = [c.id for c in level.controls if c.kind == "toggle"]
    t = theory(level.id, {"phi": 135.0, **{x: False for x in toggles}})
    assert all(o["interference"] == pytest.approx(0.0) for o in t["outcomes"])


def test_arrow_arms_are_labelled():
    t = theory("invisible-ink", {"phi": 180, "recombine": True})
    arms = sorted(a["arm"] for a in t["outcomes"][1]["arrows"])
    assert arms == ["lower", "upper"]
