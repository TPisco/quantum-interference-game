"""Game rules: is the level solved, how many stars, what feedback to show, what unlocks.

Stars (max 3 per level):
  * 1 star  - target met.
  * +1 star - met within the level's par number of runs.
  * +1 star - met on IonQ's simulator (the "IonQ seal").

Progression: level 1 is always open; solving level N unlocks level N+1.
Progress is a plain dict ``{"stars": {level_id: best_stars}, "ionq": [level_ids]}``
so the browser can store it (localStorage) and send it back.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .circuits import angle_text
from .levels import LEVELS, Level, get_level, mystery_phase


@dataclass
class Feedback:
    solved: bool
    value: float
    stars: int
    headline: str
    detail: str
    tone: str  # "success", "close", "far", "info"
    star_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"solved": self.solved, "value": self.value, "stars": self.stars,
                "headline": self.headline, "detail": self.detail, "tone": self.tone,
                "star_reasons": self.star_reasons}


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def _stars(level: Level, solved: bool, runs: int, on_ionq: bool) -> tuple[int, list[str]]:
    if not solved:
        return 0, []
    reasons = ["Target met"]
    stars = 1
    if runs <= level.par_runs:
        stars += 1
        reasons.append(f"Solved in {runs} run{'s' if runs != 1 else ''} (par {level.par_runs})")
    if on_ionq:
        stars += 1
        reasons.append("Confirmed on IonQ's simulator")
    return stars, reasons


def evaluate(level: Level, config: dict[str, Any], probabilities: dict[str, float], *,
             runs: int = 1, on_ionq: bool = False, seed: int = 0) -> Feedback:
    """Judge measured ``probabilities`` for ``level`` and write the feedback text.

    ``config`` must already be normalised (see ``circuits.normalize_config``).
    ``runs`` counts this run too.
    """
    value = level.target.value(probabilities)
    solved = level.target.met(value)
    stars, reasons = _stars(level, solved, runs, on_ionq)
    phi = float(config.get("phi", 0.0))
    writer = _WRITERS[level.id]
    headline, detail, tone = writer(level, config, value, solved, phi, seed)
    return Feedback(solved, value, stars, headline, detail, tone, reasons)


# --------------------------------------------------------------------------
# Level-specific feedback
# --------------------------------------------------------------------------

def _invisible_ink(level, cfg, value, solved, phi, seed):
    if solved:
        return ("You solved the level! Here's what your circuit did.",
                f"The first H split the qubit into two paths. Your phase P({angle_text(phi)}) "
                f"turned the lower path's arrow around, and the second H brought the paths back "
                f"together. On |0⟩ the two arrows pointed in opposite directions and cancelled "
                f"(destructive interference); on |1⟩ they lined up and added (constructive). "
                f"Result: |1⟩ in {_pct(value)} of the shots.", "success")
    if not cfg["recombine"]:
        return ("The phase is invisible!",
                f"You set φ = {angle_text(phi)}, yet the histogram still sits near 50/50, and it "
                f"would for any phase. A measurement only sees how long each amplitude arrow is, "
                f"not which way it points. Switch on the second H so the two paths meet and their "
                f"arrows can add up or cancel.", "info")
    if phi % 360 == 0:
        return ("Interference! But it favours |0⟩.",
                "With φ = 0 the second H undoes the first: both arrows add up on |0⟩ and cancel "
                "on |1⟩. You now control the interference. Use the phase to swap the winner.",
                "far")
    if value >= 0.5:
        return ("You're close.",
                f"Try adjusting the phase gate to change interference. At φ = {angle_text(phi)} "
                f"the two arrows on |1⟩ only partly line up ({_pct(value)}).", "close")
    return ("The paths interfere, but they favour |0⟩.",
            f"At φ = {angle_text(phi)} the arrows on |1⟩ still partly cancel ({_pct(value)}). "
            f"Rotate the phase further. Which angle turns + into −?", "far")


def _dark_port(level, cfg, value, solved, phi, seed):
    theta = mystery_phase(seed)
    if solved:
        leftover = ((theta + phi + 180) % 360) - 180
        return ("Dark port! You solved the level.",
                f"The mystery phase was θ = {angle_text(theta)}. With your φ = {angle_text(phi)} "
                f"the phase left between the paths is θ + φ = {leftover:+.0f}° (mod 360°), so the "
                f"two arrows on |1⟩ point in opposite directions and cancel: detector |1⟩ fired "
                f"only {_pct(value)} of the time. That is how an interferometer measures a phase.",
                "success")
    # Invert P(1) = sin^2(delta/2) to tell the player how far off they are.
    p = min(1.0, max(0.0, value))
    delta = math.degrees(2 * math.asin(math.sqrt(p)))
    if value <= 0.2:
        step = max(15, 15 * round(delta / 15))
        return ("You're close.",
                f"Detector |1⟩ still fires {_pct(value)} of the time: about ±{delta:.0f}° of phase "
                f"is left over. Try adjusting the phase gate by {step}°. One direction makes it "
                f"darker, the other brighter.", "close")
    return (f"Detector |1⟩ is lit {_pct(value)} of the time.",
            f"For this interferometer P(|1⟩) = sin²(Δ/2), where Δ = θ + φ is the phase left "
            f"between the paths. {_pct(value)} means Δ ≈ ±{delta:.0f}°. Turn φ by about "
            f"{delta:.0f}° in one direction; if it gets brighter, go the other way.", "far")


def _eraser(level, cfg, value, solved, phi, seed):
    if solved:
        return ("Information erased. You solved the level!",
                f"The CNOT had copied 'which path?' into the detector, which killed the "
                f"interference. Your eraser H sent both paths to both detector readings, so the "
                f"paths became indistinguishable again and interfered. With φ = {angle_text(phi)} "
                f"photon and detector disagreed {_pct(value)} of the time. The photon on its own "
                f"is still 50/50: the interference pattern lives in the correlation.", "success")
    if not cfg["eraser"]:
        return ("The detector knows which path the photon took.",
                f"Paths that can be told apart do not interfere, so every outcome sits near 25% "
                f"and 'disagree' near 50% whatever φ you choose ({_pct(value)} now). Erase the "
                f"which-path record: switch on the H on the detector.", "info")
    if value >= 0.5:
        return ("You're close.",
                f"Try adjusting the phase gate to change interference. The qubits disagree "
                f"{_pct(value)} of the time at φ = {angle_text(phi)}.", "close")
    return ("Interference is back, but it makes the qubits agree.",
            f"At φ = {angle_text(phi)} they disagree only {_pct(value)} of the time. Rotate the "
            f"phase to turn agreement into disagreement.", "far")


_WRITERS = {"invisible-ink": _invisible_ink, "dark-port": _dark_port, "eraser": _eraser}


# --------------------------------------------------------------------------
# Progression
# --------------------------------------------------------------------------

def new_progress() -> dict[str, Any]:
    return {"stars": {}, "ionq": []}


def clean_progress(progress: dict[str, Any] | None) -> dict[str, Any]:
    """Accept anything the browser stored; keep only valid entries."""
    out = new_progress()
    if not isinstance(progress, dict):
        return out
    stars = progress.get("stars") or {}
    if isinstance(stars, dict):
        for lid, s in stars.items():
            if lid in {lvl.id for lvl in LEVELS}:
                try:
                    out["stars"][lid] = max(0, min(3, int(s)))
                except (TypeError, ValueError):
                    pass
    ionq = progress.get("ionq") or []
    if isinstance(ionq, (list, tuple)):
        out["ionq"] = sorted({str(x) for x in ionq if str(x) in {lvl.id for lvl in LEVELS}})
    return out


def record(progress: dict[str, Any] | None, level_id: str, stars: int, on_ionq: bool) -> dict[str, Any]:
    """Return a new progress dict with this result folded in (best stars kept)."""
    out = clean_progress(progress)
    if stars > 0:
        out["stars"][level_id] = max(stars, out["stars"].get(level_id, 0))
        if on_ionq and level_id not in out["ionq"]:
            out["ionq"] = sorted(out["ionq"] + [level_id])
    return out


def unlocked(progress: dict[str, Any] | None) -> list[str]:
    """Level ids the player may open: the first one, plus one after each solved level."""
    p = clean_progress(progress)
    open_ids = []
    for i, lvl in enumerate(LEVELS):
        if i == 0 or p["stars"].get(LEVELS[i - 1].id, 0) > 0:
            open_ids.append(lvl.id)
    return open_ids


def next_level(level_id: str) -> str | None:
    ids = [lvl.id for lvl in LEVELS]
    i = ids.index(get_level(level_id).id)
    return ids[i + 1] if i + 1 < len(ids) else None
