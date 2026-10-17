"""Local development server: the real web UI, backed by real Python + Qiskit.

    python dev/server.py                      # practice + "built-in" BasicSimulator backend
    python dev/server.py --backend aer        # Qiskit Aer as the selected backend
    IONQ_API_KEY=... python dev/server.py --backend ionq [--noise aria-1]
    python dev/server.py --backend none       # like Qollab with no QPU selected
    python dev/server.py --backend fake-ionq  # UI test double for the IonQ flow (not IonQ!)

Then open http://127.0.0.1:8000/dev/index.html

How it mimics Qollab: dev/index.html maps the module name "phaseshift.api" to
dev/py-shim.js, which forwards each call to POST /api/<function>. The shim sends
the token "__qollab_backend__" wherever the page passes Qollab's `backend`, and
this server swaps in its own backend object. Every page load asks for a fresh
backend object (/api/_new_run), just as every Qollab Run creates a new one, so
the one-IonQ-job-per-Run rule behaves the same way.

Development only: binds to 127.0.0.1 and exposes a fixed allowlist of functions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phaseshift import api, execution  # noqa: E402

TOKEN = "__qollab_backend__"


class FakeIonQ:
    """UI test double for the IonQ path (``--backend fake-ionq``): named like an IonQ
    backend so the one-job-per-Run rule applies, but it runs Qiskit's local
    simulator. It is NOT IonQ; use it only to test the page flow without a key."""

    name = "fake_ionq_simulator (local test double)"

    def __init__(self):
        self._sim = execution.local_backend()

    def run(self, circuit, shots=1000, **kwargs):
        import time

        time.sleep(1.5)  # a remote job is not instant
        return self._sim.run(circuit, shots=shots)
ALLOWED = {"info", "backend_info", "default_config", "progress_status", "preview", "run_level", "sweep"}


class State:
    kind = "local"
    noise = None
    backend = None

    @classmethod
    def new_run(cls):
        if cls.kind == "none":
            cls.backend = None
        elif cls.kind == "fake-ionq":
            cls.backend = FakeIonQ()
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kwargs = {"noise_model": cls.noise} if cls.kind == "ionq" else {}
                cls.backend = execution.get_backend(cls.kind, **kwargs)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802 - http.server API
        if not self.path.startswith("/api/"):
            return self._json(404, {"ok": False, "error": "not found"})
        name = self.path[len("/api/"):].split("?")[0]
        if name == "_new_run":
            State.new_run()
            return self._json(200, {"ok": True, "backend": None if State.backend is None
                                    else execution.backend_name(State.backend)})
        if name not in ALLOWED:
            return self._json(404, {"ok": False, "error": f"unknown function {name}"})
        length = int(self.headers.get("Content-Length") or 0)
        try:
            args = json.loads(self.rfile.read(length) or b"{}").get("args", [])
        except json.JSONDecodeError:
            return self._json(400, {"ok": False, "error": "bad JSON"})
        args = [State.backend if a == TOKEN else a for a in args]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = getattr(api, name)(*args)
        return self._json(200, result)

    def log_message(self, fmt, *args):  # quieter console
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("api: " + (fmt % args) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default="local", choices=["local", "aer", "ionq", "none", "fake-ionq"],
                    help="what the page sees as Qollab's selected backend")
    ap.add_argument("--noise", default=None, help="IonQ noise model, e.g. aria-1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = ap.parse_args()
    State.kind, State.noise = args.backend, args.noise
    State.new_run()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Phase Shift dev server: http://127.0.0.1:{args.port}/dev/index.html "
          f"(backend: {args.backend})")
    server.serve_forever()


if __name__ == "__main__":
    main()
