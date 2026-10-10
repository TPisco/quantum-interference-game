"""Phase Shift: a quantum interference puzzle game built with Qiskit.

Modules
-------
levels     Level definitions (data only): gates, player controls, targets, hints.
circuits   Turn a level + player configuration into a Qiskit ``QuantumCircuit``.
paths      Exact theory: path-sum "amplitude arrows", classical vs quantum probabilities.
execution  Run circuits on a local simulator, on Qollab's injected backend, or on IonQ.
game       Solve checks, stars, feedback text and level progression.
api        JS-facing facade used by the web UI on Qollab (plain dicts, never raises).
"""

__version__ = "1.0.0"
