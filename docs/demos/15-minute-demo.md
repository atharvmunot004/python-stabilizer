# python-stabilizer — 15-Minute Demo

> Run each block top to bottom. Each section is self-contained.
> Total: ~15 minutes at a comfortable pace.

```
Install:  pip install git+https://github.com/atharvmunot004/python-stabilizer.git
Docs:     atharvmunot004.github.io/python-stabilizer
```

---

## 1 · Core State & Clifford Gates ⏱ ~2 min

The fundamental object is `StabilizerState` — a binary matrix (the *tableau*)
that encodes the quantum state in O(n²) space.

```python
from stabilizer_python import StabilizerState

# ── Construct ──────────────────────────────────────────────────────────────
st = StabilizerState.zero(3)          # |000⟩
print("n =", st.n)                    # → 3

# ── Single-qubit gates ─────────────────────────────────────────────────────
st.h(0)                               # Hadamard: |0⟩ → |+⟩
print(st.stabilizer_strings())        # → ['+XII', '+IZI', '+IIZ']

st.s(0)                               # Phase / S: X → Y
print(st.stabilizer_strings())        # → ['+YII', '+IZI', '+IIZ']

# ── Two-qubit gates ────────────────────────────────────────────────────────
st2 = StabilizerState.zero(2)
st2.h(0)
st2.cnot(0, 1)                        # Bell state
print(st2.stabilizer_strings())       # → ['+XX', '+ZZ']
print(st2.destabilizer_strings())     # → ['+ZI', '+IX']
```

**What this shows:** Every Clifford gate is a row operation on the binary tableau.
No complex arithmetic. No 2^n vector. The full state lives in 2n × (2n+1) bits.

---

## 2 · Circuit Builder ⏱ ~1 min

`Circuit` is a fluent gate builder. It separates circuit definition from state.

```python
from stabilizer_python import StabilizerState, Circuit

# Build a circuit once, run it on any state
ghz_circuit = Circuit(4).h(0).cnot(0,1).cnot(0,2).cnot(0,3)

st = StabilizerState.zero(4)
ghz_circuit.run(st)
print(st.stabilizer_strings())
# → ['+XXXX', '+ZZII', '+ZIZI', '+ZIIZ']

# Circuits can include measurements — returns outcomes as a list
st2 = StabilizerState.zero(3)
outcomes = Circuit(3).h(0).cnot(0,1).cnot(0,2).mz(0).mz(1).mz(2).run(st2)
print("GHZ measurements:", outcomes)  # always all-0 or all-1
```

**What this shows:** Circuits are composable and reusable. `run()` works on both
`StabilizerState` and `QuantumSimulator` — the same circuit object covers both modes.

---

## 3 · Tableau Inspection ⏱ ~1 min

The tableau is fully readable — every bit, every row.

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(3)
Circuit(3).h(0).cnot(0,1).cnot(0,2).run(st)   # GHZ-3

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
from stabilizer_python import StabilizerState
import random; random.seed(42)

# Deterministic measurement
st = StabilizerState.zero(2)
st.h(0); st.cnot(0, 1)               # Bell state: XX, ZZ stabilizers
print("Branch check:", st.z_measurement_branch(0))   # "random"

r0 = st.measure_z(0)
r1 = st.measure_z(1)
print(f"Outcomes: {r0}, {r1}")        # always match
print("Post-measure:", st.stabilizer_strings())

# Reset — measure + conditional X → always leaves |0⟩
st2 = StabilizerState.zero(1)
st2.h(0)                              # |+⟩ — random
outcome = st2.reset_z(0)
print(f"\nReset measured {outcome}, qubit is now:", st2.stabilizer_strings())  # always +Z
```

**What this shows:** Measurement is O(n²) Gaussian elimination on the tableau.
The branch check is free — it's O(n) and doesn't change the state.

---

## 5 · QEC Codes ⏱ ~3 min

Six named codes out of the box. All share the same API.

```python
from stabilizer_python import (
    BitFlip3Code, PhaseFlip3Code, PerfectCode,
    SteaneCode, Shor9Code, SurfaceCode3,
)

# ── All 6 codes, same interface ────────────────────────────────────────────
all_codes = [BitFlip3Code, PhaseFlip3Code, PerfectCode, SteaneCode, Shor9Code, SurfaceCode3]
print(f"{'Code':30s}  n   k   d   generators")
for c in all_codes:
    print(f"  {c.name:28s}  {c.n}   {c.k}   {c.distance()}   {len(c.generators)}")

# ── Bit-flip: inject X error, read syndrome ────────────────────────────────
print("\n--- Bit-Flip [[3,1,1]] ---")
state = BitFlip3Code.zero_state()
print("Clean:          ", BitFlip3Code.read_syndrome(state))    # [0, 0]
state.x(0)
print("After X(qubit 0):", BitFlip3Code.read_syndrome(state))  # [1, 0]
state.x(0); state.x(1)
print("After X(qubit 1):", BitFlip3Code.read_syndrome(state))  # [1, 1]

# ── Steane: CSS code, corrects both X and Z ────────────────────────────────
print("\n--- Steane [[7,1,3]] ---")
state2 = SteaneCode.zero_state()
state2.x(3)
print("Syndrome after X(3):", SteaneCode.read_syndrome(state2))
state2.x(3); state2.z(5)
print("Syndrome after Z(5):", SteaneCode.read_syndrome(state2))

# ── Perfect code: minimum code for any single-qubit error ─────────────────
print("\n--- Perfect [[5,1,3]] ---")
print("Generators:", PerfectCode.generators)
print("Logical X: ", PerfectCode.logical_x(0))
state3 = PerfectCode.zero_state()
state3.y(2)                            # arbitrary Pauli error
syn = PerfectCode.read_syndrome(state3)
print("Syndrome after Y(2):", syn)     # non-zero → detectable + correctable
```

**What this shows:** `zero_state()` builds the logical |0⟩. `read_syndrome()` extracts
the error pattern without destructive measurement. Every code exposes the same
`generators`, `logical_x()`, `logical_z()`, and `distance()` interface.

---

## 6 · Noise Channels ⏱ ~1.5 min

Pauli noise channels apply stochastic single-qubit errors.

```python
from stabilizer_python import StabilizerState, SteaneCode
from stabilizer_python.noise import (
    apply_depolarizing, apply_bit_flip_all,
    NoisyCircuit,
)
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

# ── NoisyCircuit: automatic gate-level + measurement noise ─────────────────
noisy = NoisyCircuit(n=2, gate_error=0.02, meas_error=0.03)
noisy.h(0).cnot(0, 1).mz(0).mz(1)

results = []
for _ in range(200):
    s = StabilizerState.zero(2)
    results.append(tuple(noisy.run(s)))

correlated = sum(1 for r in results if r[0] == r[1])
print(f"\nBell state: {correlated}/200 correlated outcomes (expect ~196)")
```

**What this shows:** Noise is modular — apply it before syndrome extraction in a QEC loop,
or wire it into a `NoisyCircuit` for automatic Monte Carlo simulation.

---

## 7 · Decoder Benchmarking ⏱ ~2 min

Full shot-based benchmarking: decode syndromes, count logical errors, scan thresholds.

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
from stabilizer_python import QuantumSimulator, Circuit
import math

# ── Clifford path: stays in tableau mode ───────────────────────────────────
sim = QuantumSimulator(3)
print("Initial mode:    ", sim.mode)      # "tableau"

Circuit(3).h(0).cnot(0,1).cnot(0,2).run(sim)
print("After GHZ:       ", sim.mode)      # still "tableau"
print("State:           ", sim.tableau.stabilizer_strings()[:2], "...")

# ── Non-Clifford: auto-switch to statevector ───────────────────────────────
sim2 = QuantumSimulator(2)
sim2.apply("h", [0])
print("\nBefore T gate:   ", sim2.mode)   # "tableau"

sim2.apply("t", [0])                      # T gate — not Clifford
print("After T gate:    ", sim2.mode)     # "statevector"
print("Statevector:     ", sim2.sv.to_dict())

# ── Snapshot without committing to statevector ─────────────────────────────
sim3 = QuantumSimulator(2)
Circuit(2).h(0).cnot(0,1).run(sim3)
sv = sim3.statevector_snapshot()          # converts internally, doesn't switch
print("\nSnapshot:", sv.to_dict())
print("Mode unchanged: ", sim3.mode)      # still "tableau"

# ── Parameterized rotation (non-Clifford) ─────────────────────────────────
sim4 = QuantumSimulator(1)
sim4.apply("h", [0])
sim4.apply("rz", [0], params=[math.pi/4])
print("\nRz(π/4) result:", sim4.sv.to_dict())
```

**What this shows:** One simulator handles circuits with any mix of Clifford and
non-Clifford gates. The caller never manages mode transitions. For Clifford-heavy
QEC circuits the tableau runs at full O(n²) speed; T gates fall back to exact
dense simulation.

---

## 9 · StabilizerDecomposition — T-gate Without a Statevector ⏱ ~1 min

For circuits with few T gates, the stabilizer rank decomposition is cheaper
than converting to a 2^n statevector.

```python
from stabilizer_python import StabilizerDecomposition

# Start: single stabilizer term
d = StabilizerDecomposition(3)
d.h(0); d.h(1); d.h(2)
print(f"After H gates:   {d.term_count} term   (pure Clifford)")

# Each T gate branches the state — up to doubling term count
d.t(0)
print(f"After 1 T gate:  {d.term_count} terms")

d.t(1)
print(f"After 2 T gates: {d.term_count} terms")

d.t(2)
print(f"After 3 T gates: {d.term_count} terms  (cost ~ 2^t × n²)")

# Expectation value over the superposition of branches
print(f"\n⟨Z₀⟩ = {d.expectation_z(0):.4f}")
print(f"⟨Z₁⟩ = {d.expectation_z(1):.4f}")
print(f"T count: {d.t_count}")
```

**What this shows:** Cost grows as O(2^t × n²) where t is the T-gate count —
exponential in T gates, not qubits. For circuits with many qubits but few T gates,
this is dramatically cheaper than a full 2^n statevector.

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
StabilizerState  ──gates──►  StabilizerState  ──measure──►  int (0 or 1)
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