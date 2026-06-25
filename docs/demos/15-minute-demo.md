# python-stabilizer — 15-Minute Demo

> Run each block top to bottom. Each section is self-contained.
> Total: ~15 minutes at a comfortable pace.

```
Install:  pip install git+https://github.com/atharvmunot004/python-stabilizer.git
          pip install qiskit          # optional — used in every section below
Docs:     atharvmunot004.github.io/python-stabilizer
```

Every section builds its gates in **Qiskit** first, converts with
`from_qiskit()`, then uses the library for simulation, inspection, or analysis.

---

## 1 · Core State & Clifford Gates ⏱ ~2 min

The fundamental object is `StabilizerState` — a binary matrix (the *tableau*)
that encodes the quantum state in O(n²) space.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerState
from stabilizer_python.qiskit_interop import from_qiskit

# ── Construct ──────────────────────────────────────────────────────────────
st = StabilizerState.zero(3)          # |000⟩  (state prep — not a gate)
print("n =", st.n)                    # → 3

# ── Single-qubit gates (Qiskit → from_qiskit → run) ───────────────────────
h_qc = QiskitCircuit(3)
h_qc.h(0)                             # Hadamard: |0⟩ → |+⟩
from_qiskit(h_qc).run(st)
print(st.stabilizer_strings())        # → ['+XII', '+IZI', '+IIZ']

s_qc = QiskitCircuit(3)
s_qc.s(0)                             # Phase / S: X → Y  (on current state)
from_qiskit(s_qc).run(st)
print(st.stabilizer_strings())        # → ['+YII', '+IZI', '+IIZ']

# ── Two-qubit gates ────────────────────────────────────────────────────────
st2 = StabilizerState.zero(2)
bell = QiskitCircuit(2)
bell.h(0)
bell.cx(0, 1)                         # Bell state
from_qiskit(bell).run(st2)
print(st2.stabilizer_strings())       # → ['+XX', '+ZZ']
print(st2.destabilizer_strings())     # → ['+ZI', '+IX']
```

**What this shows:** Every Clifford gate is a row operation on the binary tableau.
No complex arithmetic. No 2^n vector. The full state lives in 2n × (2n+1) bits.

---

## 2 · Circuit Builder ⏱ ~1 min

Define gates in Qiskit, convert once with `from_qiskit()`, then `run()` on any
state or simulator.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerState
from stabilizer_python.qiskit_interop import from_qiskit

# ── GHZ-4 in Qiskit ────────────────────────────────────────────────────────
ghz_qc = QiskitCircuit(4)
ghz_qc.h(0)
ghz_qc.cx(0, 1)
ghz_qc.cx(0, 2)
ghz_qc.cx(0, 3)
ghz_circuit = from_qiskit(ghz_qc)

st = StabilizerState.zero(4)
ghz_circuit.run(st)
print(st.stabilizer_strings())
# → ['+XXXX', '+ZZII', '+ZIZI', '+ZIIZ']

# ── GHZ-3 with measurements ────────────────────────────────────────────────
meas_qc = QiskitCircuit(3, 3)
meas_qc.h(0)
meas_qc.cx(0, 1)
meas_qc.cx(0, 2)
meas_qc.measure(0, 0)
meas_qc.measure(1, 1)
meas_qc.measure(2, 2)
meas_circuit = from_qiskit(meas_qc)

st2 = StabilizerState.zero(3)
outcomes = meas_circuit.run(st2)
print("GHZ measurements:", outcomes)  # always all-0 or all-1
```

**What this shows:** Qiskit circuits convert to the local `Circuit` type.
`run()` works on both `StabilizerState` and `QuantumSimulator` — the same
converted circuit covers both modes.

---

## 3 · Tableau Inspection ⏱ ~1 min

The tableau is fully readable — every bit, every row.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerState
from stabilizer_python.qiskit_interop import from_qiskit

ghz_qc = QiskitCircuit(3)
ghz_qc.h(0)
ghz_qc.cx(0, 1)
ghz_qc.cx(0, 2)

st = StabilizerState.zero(3)
from_qiskit(ghz_qc).run(st)           # GHZ-3

# ── String views ───────────────────────────────────────────────────────────
print("Stabilizers:  ", st.stabilizer_strings())
print("Destabilizers:", st.destabilizer_strings())

# ── Raw binary matrix ──────────────────────────────────────────────────────
print("\nX matrix:", st.x_mat[st.n:])    # bottom-n rows = stabilizers
print("Z matrix:", st.z_mat[st.n:])
print("Phase:   ", st.r_phase[st.n:])

# ── Formatted debug output ─────────────────────────────────────────────────
print()
print(st.format_xz_binary_matrices())   # full 2n × (2n+1) table

# ── Invariant check ────────────────────────────────────────────────────────
st._check_tableau_invariants()          # asserts independence + commutativity
print("Invariants hold.")
```

**What this shows:** The stabilizer formalism is completely transparent.
The measurement branch can be predicted, proofs can be verified, and
the raw data can be handed off to any downstream analysis.

---

## 4 · Measurement ⏱ ~1 min

`measure_z` collapses the tableau and returns 0 or 1.
`z_measurement_branch` tells you whether the outcome will be random *before* measuring.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerState
from stabilizer_python.qiskit_interop import from_qiskit
import random; random.seed(42)

# Deterministic measurement — Bell state from Qiskit
bell = QiskitCircuit(2)
bell.h(0)
bell.cx(0, 1)

st = StabilizerState.zero(2)
from_qiskit(bell).run(st)              # stabilizers: +XX, +ZZ
print("Branch check:", st.z_measurement_branch(0))   # "random"

r0 = st.measure_z(0)
r1 = st.measure_z(1)
print(f"Outcomes: {r0}, {r1}")        # always match
print("Post-measure:", st.stabilizer_strings())

# Reset — measure + conditional X → always leaves |0⟩
st2 = StabilizerState.zero(1)
plus = QiskitCircuit(1)
plus.h(0)                             # |+⟩ — random
from_qiskit(plus).run(st2)
outcome = st2.reset_z(0)
print(f"\nReset measured {outcome}, qubit is now:", st2.stabilizer_strings())  # always +Z
```

**What this shows:** Measurement is O(n²) Gaussian elimination on the tableau.
The branch check is free — it's O(n) and doesn't change the state.

---

## 5 · QEC Codes ⏱ ~3 min

Six named codes out of the box. All share the same API. Pauli errors are applied
via small Qiskit circuits converted with `from_qiskit()`.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import (
    BitFlip3Code, PhaseFlip3Code, PerfectCode,
    SteaneCode, Shor9Code, SurfaceCode3,
)
from stabilizer_python.qiskit_interop import from_qiskit

# ── All 6 codes, same interface ────────────────────────────────────────────
all_codes = [BitFlip3Code, PhaseFlip3Code, PerfectCode, SteaneCode, Shor9Code, SurfaceCode3]
print(f"{'Code':30s}  n   k   d   generators")
for c in all_codes:
    print(f"  {c.name:28s}  {c.n}   {c.k}   {c.distance()}   {len(c.generators)}")

# ── Bit-flip: inject X error, read syndrome ────────────────────────────────
print("\n--- Bit-Flip [[3,1,1]] ---")
state = BitFlip3Code.zero_state()
print("Clean:          ", BitFlip3Code.read_syndrome(state))    # [0, 0]

err = QiskitCircuit(3)
err.x(0)
from_qiskit(err).run(state)
print("After X(qubit 0):", BitFlip3Code.read_syndrome(state))  # [1, 0]

err2 = QiskitCircuit(3)
err2.x(0)
err2.x(1)
from_qiskit(err2).run(state)
print("After X(qubit 1):", BitFlip3Code.read_syndrome(state))  # [1, 1]

# ── Steane: CSS code, corrects both X and Z ────────────────────────────────
print("\n--- Steane [[7,1,3]] ---")
state2 = SteaneCode.zero_state()
x_err = QiskitCircuit(7)
x_err.x(3)
from_qiskit(x_err).run(state2)
print("Syndrome after X(3):", SteaneCode.read_syndrome(state2))

z_err = QiskitCircuit(7)
z_err.z(5)
from_qiskit(z_err).run(state2)
print("Syndrome after Z(5):", SteaneCode.read_syndrome(state2))

# ── Perfect code: minimum code for any single-qubit error ─────────────────
print("\n--- Perfect [[5,1,3]] ---")
print("Generators:", PerfectCode.generators)
print("Logical X: ", PerfectCode.logical_x(0))
state3 = PerfectCode.zero_state()
y_err = QiskitCircuit(5)
y_err.y(2)                            # arbitrary Pauli error
from_qiskit(y_err).run(state3)
syn = PerfectCode.read_syndrome(state3)
print("Syndrome after Y(2):", syn)     # non-zero → detectable + correctable
```

**What this shows:** `zero_state()` builds the logical |0⟩. `read_syndrome()` extracts
the error pattern without destructive measurement. Qiskit Pauli gates convert cleanly
and run on encoded states the same way as native gate calls.

---

## 6 · Noise Channels ⏱ ~1.5 min

Pauli noise channels apply stochastic single-qubit errors. Gate sequences come
from Qiskit via `from_qiskit()`.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerState, SteaneCode
from stabilizer_python.noise import (
    apply_depolarizing, apply_bit_flip_all,
    NoisyCircuit,
)
from stabilizer_python.qiskit_interop import from_qiskit
import random; random.seed(7)

# ── Single-qubit depolarizing ──────────────────────────────────────────────
st = StabilizerState.zero(7)
error = apply_depolarizing(st, qubit=0, p=0.15)
print("Applied to qubit 0:", error)    # 'I', 'X', 'Y', or 'Z'

# ── All-qubit channel ──────────────────────────────────────────────────────
state = SteaneCode.zero_state()
errors = apply_bit_flip_all(state, p=0.05)
print("Errors across 7 qubits:", errors)
print("Syndrome:", SteaneCode.read_syndrome(state))

# ── NoisyCircuit: Qiskit Bell prep + automatic gate/measurement noise ──────
bell_qc = QiskitCircuit(2)
bell_qc.h(0)
bell_qc.cx(0, 1)

noisy = NoisyCircuit(n=2, gate_error=0.02, meas_error=0.03)
noisy.extend(from_qiskit(bell_qc).ops)   # reuse converted gate list
noisy.mz(0).mz(1)

results = []
for _ in range(200):
    s = StabilizerState.zero(2)
    results.append(tuple(noisy.run(s)))

correlated = sum(1 for r in results if r[0] == r[1])
print(f"\nBell state: {correlated}/200 correlated outcomes (expect ~196)")
```

**What this shows:** Noise is modular — apply it before syndrome extraction in a QEC loop,
or wire a `from_qiskit()` gate list into `NoisyCircuit` for automatic Monte Carlo simulation.

---

## 7 · Decoder Benchmarking ⏱ ~2 min

Full shot-based benchmarking: decode syndromes, count logical errors, scan thresholds.
This section uses the code and noise API directly (no gate circuit).

```python
from stabilizer_python import SteaneCode, build_lookup_decoder, benchmark_code, threshold_scan
from stabilizer_python.noise import apply_bit_flip_all

# ── Build a lookup decoder ─────────────────────────────────────────────────
decoder = build_lookup_decoder(SteaneCode)  # enumerate all weight-1 errors

# ── Single benchmark run ───────────────────────────────────────────────────
result = benchmark_code(
    SteaneCode,
    noise_model=lambda st: apply_bit_flip_all(st, p=0.05),
    decoder=decoder,
    n_shots=400,
    seed=42,
)
print(result.summary())
# → n_shots, logical_error_rate, x/z error rates, throughput

# ── Threshold scan: sweep physical error rates ─────────────────────────────
scan = threshold_scan(
    SteaneCode,
    noise_model_factory=lambda p: (lambda st: apply_bit_flip_all(st, p=p)),
    decoder=decoder,
    p_values=[0.01, 0.03, 0.05, 0.08, 0.12],
    n_shots_per_p=200,
    seed=1,
)
print("\np_phys → p_logical:")
for p, rate in zip(scan.p_values, scan.logical_error_rates):
    bar = "█" * int(rate * 50)
    print(f"  {p:.2f}  →  {rate:.4f}  {bar}")
```

**What this shows:** `benchmark_code` is a full Monte Carlo QEC simulation loop.
`threshold_scan` sweeps physical error rates to find where logical error rate rises —
the threshold is where the code stops providing an advantage.

---

## 8 · Hybrid Simulation ⏱ ~1.5 min

`QuantumSimulator` starts in tableau mode and switches to statevector
automatically on the first non-Clifford gate.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit
import math

# ── Clifford path: stays in tableau mode ───────────────────────────────────
ghz_qc = QiskitCircuit(3)
ghz_qc.h(0)
ghz_qc.cx(0, 1)
ghz_qc.cx(0, 2)

sim = QuantumSimulator(3)
print("Initial mode:    ", sim.mode)      # "tableau"

from_qiskit(ghz_qc).run(sim)
print("After GHZ:       ", sim.mode)      # still "tableau"
print("State:           ", sim.tableau.stabilizer_strings()[:2], "...")

# ── Non-Clifford: auto-switch to statevector ───────────────────────────────
t_qc = QiskitCircuit(2)
t_qc.h(0)
t_qc.t(0)

sim2 = QuantumSimulator(2)
print("\nBefore T gate:   ", sim2.mode)   # "tableau"
from_qiskit(t_qc).run(sim2)               # H stays tableau; T triggers switch
print("After T gate:    ", sim2.mode)     # "statevector"
print("Statevector:     ", sim2.sv.to_dict())

# ── Snapshot without committing to statevector ─────────────────────────────
bell_qc = QiskitCircuit(2)
bell_qc.h(0)
bell_qc.cx(0, 1)

sim3 = QuantumSimulator(2)
from_qiskit(bell_qc).run(sim3)
sv = sim3.statevector_snapshot()          # converts internally, doesn't switch
print("\nSnapshot:", sv.to_dict())
print("Mode unchanged: ", sim3.mode)      # still "tableau"

# ── Parameterized rotation (non-Clifford) ─────────────────────────────────
rz_qc = QiskitCircuit(1)
rz_qc.h(0)
rz_qc.rz(math.pi / 4, 0)

sim4 = QuantumSimulator(1)
from_qiskit(rz_qc).run(sim4)
print("\nRz(π/4) result:", sim4.sv.to_dict())
```

**What this shows:** One simulator handles circuits with any mix of Clifford and
non-Clifford gates. The caller never manages mode transitions. For Clifford-heavy
QEC circuits the tableau runs at full O(n²) speed; T gates fall back to exact
dense simulation.

---

## 9 · StabilizerDecomposition — T-gate Without a Statevector ⏱ ~1 min

For circuits with few T gates, the stabilizer rank decomposition is cheaper
than converting to a 2^n statevector. A non-Clifford state has **no single**
stabilizer description — but each branch of the decomposition does.

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import StabilizerDecomposition
from stabilizer_python.qiskit_interop import from_qiskit

def run_on_decomp(d, circuit):
    """Replay a from_qiskit() circuit on StabilizerDecomposition."""
    for op in circuit.ops:
        if op.gate_obj is not None:
            g, t = op.gate_obj, list(op.targets)
            if g.num_qubits == 1:
                getattr(d, g.name)(t[0])
            else:
                getattr(d, g.name)(*t)
        elif op.name == "H":
            d.h(op.targets[0])
        elif op.name == "S":
            d.s(op.targets[0])
        elif op.name == "X":
            d.x(op.targets[0])
        elif op.name == "Z":
            d.z(op.targets[0])
        elif op.name == "CNOT":
            d.cnot(op.targets[0], op.targets[1])

# ── 2-qubit circuit in Qiskit: Clifford prep, then two T gates ─────────────
qc = QiskitCircuit(2)
qc.h(0)
qc.h(1)

d = StabilizerDecomposition(2)
run_on_decomp(d, from_qiskit(qc))
print(f"After Clifford prep: {d.term_count} term")
print(f"  stabilizers: {d.terms[0][1].stabilizer_strings()}")   # ['+XI', '+IX']

# Each T gate branches into Z=+1 and Z=-1 eigenspaces — up to doubling terms
qc.t(0)
qc.cx(0, 1)
d = StabilizerDecomposition(2)
run_on_decomp(d, from_qiskit(qc))
print(f"\nAfter T + CNOT:      {d.term_count} terms")
for i, (coeff, state) in enumerate(d.terms):
    print(f"  term {i}: α={coeff:.4f}  gens={state.stabilizer_strings()}")

qc.t(1)
d = StabilizerDecomposition(2)
run_on_decomp(d, from_qiskit(qc))
print(f"\nAfter 2nd T gate:      {d.term_count} terms  (2^t = 2²)")
print(d.summary())   # each branch lists its own stabilizer generators

# Expectation values over the weighted sum of branches
print(f"\n⟨Z₀⟩ = {d.expectation_z(0):.4f}")
print(f"⟨Z₁⟩ = {d.expectation_z(1):.4f}")
print(f"T count: {d.t_count}")
```

**What this shows:** A T gate on a stabilizer state splits it into branches, each
with its own Pauli stabilizer generators (`+ZI`, `-IZ`, …). The full state is a
*sum* of stabilizer states, not a stabilizer state itself — that is why
`QuantumSimulator` falls back to a statevector after a T gate. Cost grows as
O(2^t × n²) in the T-gate count t, not in qubits n, so this stays cheap for
wide circuits with few T gates.

---

## Package Map

```
stabilizer_python/
│
├── tableau.py          StabilizerState — the CHP binary tableau
├── circuit.py          Circuit — fluent gate builder (30+ ops)
├── stabilizer_code.py  StabilizerCode — [[n,k,d]] from Pauli generators
│                       ↳ BitFlip3, PhaseFlip3, Perfect, Steane, Shor9, Surface3
│
├── syndrome.py         read_syndrome(), SyndromeExtractor, parity checks
├── noise.py            Pauli channels, NoisyCircuit, run_shots()
├── benchmark.py        benchmark_code(), threshold_scan(), compare_codes()
│
├── simulator.py        QuantumSimulator — hybrid Clifford / statevector
├── decomposition.py    StabilizerDecomposition — T-gate via stabilizer rank
│
├── qiskit_interop.py   from_qiskit() — convert any Qiskit circuit
├── encoded_state.py    EncodedState — logical operator tracking
├── statevector.py      Statevector — dense backend, tableau_to_statevector()
└── tracing.py          TracedCircuit — step-by-step tableau recording
```

**Core data flow:**

```
Qiskit QuantumCircuit  ──from_qiskit()──►  Circuit  ──run()──►  StabilizerState / QuantumSimulator
      │                            │
      │ zero_state()               │ read_syndrome()
      ▼                            ▼
 StabilizerCode              [syndrome bits]
                                   │
                             build_lookup_decoder()
                                   │
                             benchmark_code() ──► CodeBenchmarkResult
                             threshold_scan() ──► ThresholdScanResult
```
