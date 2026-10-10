"""Regenerate and execute notebooks/phase_shift_walkthrough.ipynb (needs nbformat, nbclient, ipykernel, matplotlib)."""
import nbformat as nbf
from nbclient import NotebookClient
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
md("""# Phase Shift: the physics behind the game

This notebook walks through the five levels of **Phase Shift** with plain Qiskit, then shows the
"amplitude arrows" the game draws, and how to run the same circuits on IonQ's simulator.

* On **Qollab** the game itself is the web page (`index.html` + `main.js`); this notebook is a
  companion for teachers and developers. It runs with Qiskit's built-in simulator, no extras needed.
* Locally: `pip install -r requirements-dev.txt`, then open this notebook from the repository root."""),
code("""import math, os, sys
sys.path.insert(0, os.path.abspath(".."))  # the repository root, when run from notebooks/
from qiskit import QuantumCircuit
from qiskit.providers.basic_provider import BasicSimulator
from phaseshift import circuits, execution, paths
from phaseshift.levels import get_level, mystery_phase

sim = BasicSimulator()
def run(qc, shots=2000):
    return execution.to_probabilities(execution.run_circuit(sim, qc, shots=shots, seed=7))"""),
md("""## 1. Superposition: H splits the qubit into two paths
Measuring right after a Hadamard gives 50/50."""),
code("""qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)
print(qc.draw())
run(qc)"""),
md("""## 2. Level 1, *Invisible Ink*: a phase alone is invisible
Add a phase gate P(φ) after the split. Whatever φ is, the counts stay at 50/50, because a measurement only sees the
length of each amplitude arrow, and P(φ) only rotates one of them. (The simulator seed is fixed, so the counts
come out identical to the last shot: the phase changes nothing a measurement can see.)"""),
code("""lvl = get_level("invisible-ink")
for phi in (0, 45, 90, 180, 270):
    probs = run(circuits.build_circuit(lvl, {"phi": phi, "recombine": False}))
    print(f"phi = {phi:3d}°  ->  P(|1>) = {probs['1']:.3f}")"""),
md("""### Recombine the paths with a second H: now the phase decides
Theory: P(|1⟩) = sin²(φ/2). The sweep below runs the circuit for every dial position."""),
code("""rows = []
for k in range(25):
    phi = 15 * k
    measured = run(circuits.build_circuit(lvl, {"phi": phi % 360, "recombine": True}))["1"]
    rows.append((phi, measured, math.sin(math.radians(phi) / 2) ** 2))
for phi, m, t in rows[::3]:
    print(f"phi = {phi:3d}°  measured {m:.3f}   theory {t:.3f}")"""),
code("""%matplotlib inline
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.plot([r[0] for r in rows], [r[2] for r in rows], label="theory sin²(φ/2)", color="#1f77b4")
ax.scatter([r[0] for r in rows], [r[1] for r in rows], label="measured (2000 shots)", color="#ff7f0e", zorder=3)
ax.axhline(0.5, ls=":", color="gray", label="phase alone (no recombination)")
ax.set_xlabel("phase φ (degrees)"); ax.set_ylabel("P(|1⟩)"); ax.set_xticks(range(0, 361, 45))
ax.legend(loc="center right", fontsize=8); ax.set_title("Interference fringe: H · P(φ) · H")
fig.tight_layout()
plt.show()"""),
md("""## 3. The arrows: classical vs quantum
`phaseshift.paths` enumerates every path through the circuit and its amplitude. Quantum probability = |sum of arrows|²;
classical = sum of |arrow|². The difference is the interference term the game shows for each outcome."""),
code("""qc = circuits.build_circuit(lvl, {"phi": 180, "recombine": True}, measure=False)
for o in paths.analyze(qc)["outcomes"]:
    arrows = ", ".join(f"{a['arm']}: {complex(a['re'], a['im']):.2f}" for a in o["arrows"])
    print(f"{o['label']}: arrows [{arrows}]  classical {o['classical']:.2f}  quantum {o['theory']:.2f}  interference {o['interference']:+.2f}")"""),
md("""## 4. Level 2, *Dark Port*: measuring a hidden phase
A mystery phase θ sits on the lower path. P(|1⟩) = sin²((θ + φ)/2), so one measurement gives |θ + φ| and a second
one tells the sign. Here is the two-run strategy the par is based on."""),
code("""dark = get_level("dark-port"); seed = 2026
p1 = run(circuits.build_circuit(dark, {"phi": 0}, seed=seed))["1"]
delta = math.degrees(2 * math.asin(math.sqrt(p1)))
print(f"run 1: phi = 0 -> P(|1>) = {p1:.3f}  =>  leftover phase ≈ ±{delta:.0f}°")
guess = (-round(delta / 15) * 15) % 360
p2 = run(circuits.build_circuit(dark, {"phi": guess}, seed=seed))["1"]
if p2 > 0.05:
    guess = (round(delta / 15) * 15) % 360
    p2 = run(circuits.build_circuit(dark, {"phi": guess}, seed=seed))["1"]
print(f"answer: phi = {guess}° -> P(|1>) = {p2:.3f}   (the hidden theta was {mystery_phase(seed)}°)")"""),
md("""## 5. Level 3, *Which-Path Eraser*: interference moves into correlations"""),
code("""er = get_level("eraser")
for eraser in (False, True):
    qc = circuits.build_circuit(er, {"phi": 180, "eraser": eraser})
    probs = run(qc)
    disagree = probs["01"] + probs["10"]
    photon = paths.marginal(probs, 0, 2)["1"]
    print(f"eraser {'on ' if eraser else 'off'}: P(disagree) = {disagree:.3f}, photon alone P(1) = {photon:.3f}")
print(circuits.build_circuit(er, {"phi": 180, "eraser": True}).draw())"""),
md("""## 6. Level 4, *Kickback*: the phase lands on the control
A controlled phase CP(φ) adds φ only where both qubits are 1. With the target in |0⟩ nothing happens; flip the target
to |1⟩ and the phase "kicks back" onto the control, where the second H turns it into a bit. The target never changes."""),
code("""kb = get_level("kickback")
for flip in (False, True):
    probs = run(circuits.build_circuit(kb, {"phi": 180, "flip": flip}))
    control = paths.marginal(probs, 0, 2)["1"]
    target = paths.marginal(probs, 1, 2)["1"]
    print(f"flip {'on ' if flip else 'off'}: P(control = 1) = {control:.3f}, P(target = 1) = {target:.3f}")
print(circuits.build_circuit(kb, {"phi": 180, "flip": True}).draw())"""),
md("""## 7. Level 5, *Amplifier*: Grover search on two qubits
Mark door |11⟩ with a phase φ, then apply the diffuser (reflection about the average amplitude).
With the diffuser on, P(|11⟩) = (10 − 6 cos φ)/16, which reaches 1 at φ = 180°: one oracle query finds the prize.
The arrows explain it: four paths land on every door; on |11⟩ they line up, elsewhere they cancel in pairs."""),
code("""amp = get_level("amplifier")
for phi in (0, 90, 135, 180):
    p11 = run(circuits.build_circuit(amp, {"phi": phi, "diffuser": True}))["11"]
    print(f"phi = {phi:3d}°: P(|11>) = {p11:.3f}   theory {(10 - 6 * math.cos(math.radians(phi))) / 16:.3f}")
qc = circuits.build_circuit(amp, {"phi": 180, "diffuser": True}, measure=False)
for o in paths.analyze(qc)["outcomes"]:
    arrows = ", ".join(f"{a['re']:+.2f}" for a in o["arrows"])
    print(f"{o['label']}: arrows [{arrows}] -> sum {o['sum']['re']:+.2f}, P = {o['theory']:.2f}")"""),
md("""## 8. Running on IonQ's simulator

**On Qollab** you do not create a backend: press **Run**, pick IonQ's simulator in *Select QPU*, and the platform
passes a `backend` object to the page; `phaseshift.api.run_level(backend, ...)` submits one single-circuit job.

**Locally** (outside Qollab) use `qiskit-ionq` with your own key: `export IONQ_API_KEY=...`. The cell below only
runs if a key is set. `noise_model="aria-1"` or `"forte-1"` adds IonQ's hardware noise model to the simulator."""),
code("""if os.environ.get("IONQ_API_KEY"):
    ionq = execution.ionq_backend()  # or execution.ionq_backend(noise_model="aria-1")
    qc = circuits.build_circuit(lvl, {"phi": 180, "recombine": True})
    print(execution.to_probabilities(execution.run_circuit(ionq, qc, shots=1000)))
else:
    print("IONQ_API_KEY not set: skipping the IonQ cell. On Qollab, select IonQ in 'Select QPU' instead.")"""),
md("""## 9. Same thing through the game API
This is the exact call the web page makes (with `where="backend"` it would use Qollab's selected backend)."""),
code("""from phaseshift import api
res = api.run_level(None, "eraser", {"phi": 180, "eraser": True}, {"where": "local", "shots": 1000})
print(res["feedback"]["headline"]); print(res["feedback"]["detail"])"""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}, "language_info": {"name": "python"}})
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
nbf.write(nb, str(ROOT / "notebooks" / "phase_shift_walkthrough.ipynb"))
for c in nb.cells:
    if c.cell_type == "code":
        for o in c.get("outputs", []):
            if o.get("output_type") == "error": print("ERROR", o["ename"], o["evalue"])
print("ok")
