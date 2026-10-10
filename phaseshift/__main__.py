"""Command-line runner: play or verify Phase Shift levels without the web UI.

Examples::

    python -m phaseshift                       # every level: wrong try + solution, local simulator
    python -m phaseshift --backend aer
    IONQ_API_KEY=... python -m phaseshift --backend ionq [--noise aria-1]
    python -m phaseshift --level invisible-ink --phi 180 --on recombine
"""

from __future__ import annotations

import argparse
import sys

from . import api, circuits, execution
from .levels import LEVELS, get_level, mystery_phase

SOLUTIONS = {
    "invisible-ink": lambda seed: {"phi": 180, "recombine": True},
    "dark-port": lambda seed: {"phi": (360 - mystery_phase(seed)) % 360},
    "eraser": lambda seed: {"phi": 180, "eraser": True},
    "kickback": lambda seed: {"phi": 180, "flip": True},
    "amplifier": lambda seed: {"phi": 180, "diffuser": True},
}


def _bar(p: float, width: int = 30) -> str:
    return "█" * round(p * width) + "·" * (width - round(p * width))


def show(result: dict) -> None:
    if not result["ok"]:
        print(f"  ERROR [{result.get('code')}]: {result['error']}")
        return
    print(f"  backend: {result['source']['name']}  shots: {result['shots']}  "
          f"({result['source']['seconds']} s)")
    for o in result["outcomes"]:
        theory = f"  theory {o['theory']:.3f}  classical {o['classical']:.3f}" if "theory" in o else ""
        mark = "◎" if o["is_target"] else " "
        print(f"  {mark} {o['label']:>24}  {_bar(o['measured'])}  {o['measured']:.3f}{theory}")
    fb = result["feedback"]
    print(f"  → {fb['headline']}  ({'★' * fb['stars'] or 'no stars'})")
    print(f"    {fb['detail']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m phaseshift", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default="local", choices=["local", "aer", "ionq"])
    ap.add_argument("--noise", default=None, help="IonQ noise model, e.g. aria-1 or forte-1")
    ap.add_argument("--shots", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=7, help="attempt seed (Dark Port's hidden phase)")
    ap.add_argument("--level", choices=[lvl.id for lvl in LEVELS])
    ap.add_argument("--phi", type=float, help="your phase in degrees")
    ap.add_argument("--on", action="append", default=[], help="switch a toggle on (repeatable)")
    args = ap.parse_args(argv)

    kwargs = {"noise_model": args.noise} if args.backend == "ionq" else {}
    # A fresh backend object per run: the API allows one IonQ job per backend object
    # (Qollab's rule); outside Qollab qiskit-ionq has no such limit.
    def backend():
        return execution.get_backend(args.backend, **kwargs)

    where = "local" if args.backend == "local" else "backend"
    opts = {"where": where, "shots": args.shots, "seed": args.seed}

    if args.level:
        level = get_level(args.level)
        cfg = level.default_config()
        if args.phi is not None:
            cfg["phi"] = args.phi
        for t in args.on:
            cfg[t] = True
        print(f"Level {level.number}: {level.title}\n{circuits.circuit_text(level, cfg, seed=args.seed)}")
        show(api.run_level(backend(), level.id, cfg, opts))
        return 0

    for level in LEVELS:
        print(f"\n=== Level {level.number}: {level.title} ({level.concept})")
        print(f"Target: {level.target.description}")
        tries = [("first try (defaults)", level.default_config()),
                 ("solution", SOLUTIONS[level.id](args.seed))]
        for i, (label, cfg) in enumerate(tries):
            print(f"\n-- {label}: {cfg}")
            print(circuits.circuit_text(level, cfg, seed=args.seed))
            show(api.run_level(backend(), level.id, cfg, {**opts, "runs_before": i}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
