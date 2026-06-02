# Getting Started

This guide walks from installation to the core workflows: preparing tableau states, running Clifford circuits, switching automatically to statevector simulation for non-Clifford gates, loading circuits from Qiskit, measuring qubits, running the included QEC examples, and validating the checkout.

## Installation

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

With dev dependencies (pytest + Qiskit interop tests):

```bash
pip install "stabilizer-python[dev] @ git+https://github.com/atharvmunot004/python-stabilizer.git"
```

Requirements: Python `>=3.9`. The runtime package has no required third-party dependencies. NumPy is used automatically when the hybrid statevector backend is active; it is not required for pure Clifford circuits.

Source links:

- Repository: [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer)
- Package metadata: [`pyproject.toml`](https://github.com/atharvmunot004/python-stabilizer/blob/main/pyproject.toml)
- Public exports: [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py)

---

## Simulation backends at a glance

| Backend | Class | State | Gate scope | Per-gate cost |
|---|---|---|---|---|
| Tableau | `StabilizerState` | 2n×n binary tableau | Clifford only | O(n) |
| Hybrid | `QuantumSimulator` | Tableau until first non-Clifford gate, then 2^n statevector | Full Qiskit gate set | O(n) Clifford, O(2^n) after switch |

Use `StabilizerState` directly for pure Clifford and QEC workflows. Use `QuantumSimulator` when a circuit may contain `T`, rotations, Toffoli, or gates loaded from Qiskit.

---

## Your first stabilizer state

```python
from stabilizer_python import StabilizerState

# 2-qubit zero state |00>
st = StabilizerState.zero(2)
print(st.format_chp_printstate())
```

```
+XI
+IX
-----------
+ZI
+IZ
```

The top half are destabilizers, the bottom half are stabilizer generators. See [The Tableau Representation](theory/tableau.md) for what these mean and [`StabilizerState.zero`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) for the initialization logic.

---

## Building Clifford circuits

`Circuit` is a fluent gate builder implemented in [`circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py). It records operations and applies them to a `StabilizerState` or `QuantumSimulator` when `run(state)` is called.

```python
from stabilizer_python import StabilizerState, Circuit

# Bell state
st = StabilizerState.zero(2)
c = Circuit(2).h(0).cnot(0, 1)
c.run(st)

print(st.format_chp_printstate())
# +XX
# +ZZ   stabilizers of |Phi+>
```

Available Clifford circuit methods:

| Method | Gate |
|---|---|
| `.h(q)` | Hadamard |
| `.s(q)` | Phase (`S`) |
| `.sdg(q)` | `S` dagger |
| `.sx(q)` | Square-root X |
| `.sxdg(q)` | Square-root X dagger |
| `.x(q)` | Pauli `X` |
| `.y(q)` | Pauli `Y` |
| `.z(q)` | Pauli `Z` |
| `.i(q)` | Identity |
| `.cnot(c, t)` / `.cx(c, t)` | Controlled-NOT |
| `.cz(c, t)` | Controlled-Z |
| `.cy(c, t)` | Controlled-Y |
| `.ch(c, t)` | Controlled-H |
| `.swap(q1, q2)` | SWAP |
| `.iswap(q1, q2)` | iSWAP |
| `.cs(c, t)` | Controlled-S |
| `.csdg(c, t)` | Controlled-S dagger |
| `.ecr(q1, q2)` | Echoed cross-resonance |
| `.dcx(q1, q2)` | Double-CNOT |
| `.mz(q)` | Measure Z |

The `run(state)` method returns a list of measurement outcomes, one per `.mz()` call.

---

## Non-Clifford gates with QuantumSimulator

`QuantumSimulator` starts in tableau mode and switches to statevector mode on the first non-Clifford gate.

```python
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(1)
sim.apply("h", [0])      # stays in tableau mode
sim.apply("t", [0])      # triggers switch to statevector
print(sim.mode)          # "statevector"
print(sim.sv.data)       # [0.70710678+0.j  0.5       +0.5j]
```

Single-qubit rotations use concrete numeric parameters:

```python
from stabilizer_python import QuantumSimulator
import math

sim = QuantumSimulator(1)
sim.apply("rx", [0], params=[math.pi / 4])
sim.apply("ry", [0], params=[math.pi / 5])
sim.apply("rz", [0], params=[math.pi / 6])
sim.apply("p", [0], params=[math.pi / 7])
sim.apply("u", [0], params=[math.pi / 4, math.pi / 3, math.pi / 8])
print(sim.sv.to_dict())
```

Two-qubit parameterized gates use the same name-based interface:

```python
from stabilizer_python import QuantumSimulator
import math

sim = QuantumSimulator(2)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("crz", [0, 1], params=[math.pi / 3])
sim.apply("rzz", [0, 1], params=[math.pi / 4])
sim.apply("rxx", [0, 1], params=[math.pi / 5])
print(sim.sv.probabilities())
```

Toffoli is a three-qubit non-Clifford gate. This prepares `|110>` in the displayed bitstring convention, then flips the target to `|111>`.

```python
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(3)
sim.apply("x", [1])
sim.apply("x", [2])
sim.apply("ccx", [1, 2, 0])
print(sim.statevector_snapshot().to_dict())  # {'111': (1+0j)}
```

`Circuit` can also contain non-Clifford gates and run directly on a `QuantumSimulator`.

```python
from stabilizer_python import Circuit, QuantumSimulator
import math

circuit = Circuit(3).h(0).t(0).rx(math.pi / 4, 1).ccx(0, 1, 2)

sim = QuantumSimulator(3)
circuit.run(sim)
print(sim.mode)      # "statevector"
print(sim.sv.data)
```

For lower-level code, pass a `Gate` object with `.apply_gate()`.

```python
from stabilizer_python import QuantumSimulator, RZGate
import math

sim = QuantumSimulator(1)
sim.apply_gate(RZGate(math.pi / 3), [0])
print(sim.sv.data)
```

---

## Loading circuits from Qiskit

Install Qiskit separately when you want to load Qiskit circuits:

```bash
pip install qiskit
```

Qiskit is an optional dependency. The runtime package does not require it for local circuits.

Example 1 - pure Clifford Qiskit circuit, which stays in tableau mode:

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2)
qc.h(0)
qc.cx(0, 1)

sim = QuantumSimulator(2)
from_qiskit(qc).run(sim)

print(sim.mode)                              # "tableau"
print(sim.statevector_snapshot().to_dict()) # {'00': ..., '11': ...}
```

Example 2 - non-Clifford Qiskit circuit, which triggers statevector mode:

```python
import math
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2)
qc.h(0)
qc.t(0)
qc.cx(0, 1)
qc.rz(math.pi / 4, 1)

sim = QuantumSimulator(2)
from_qiskit(qc).run(sim)

print(sim.mode)       # "statevector"
print(sim.sv.data)
```

Example 3 - 3-qubit QFT from Qiskit's circuit library:

```python
from qiskit.circuit.library import QFT
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QFT(3, do_swaps=True).decompose()

sim = QuantumSimulator(3)
from_qiskit(qc).run(sim)

print(sim.sv.probabilities())   # approximately uniform across 8 basis states
```

Example 4 - parameterized VQE ansatz with bound parameters:

```python
from qiskit.circuit.library import RealAmplitudes
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit
import math

ansatz = RealAmplitudes(2, reps=1)
bound = ansatz.assign_parameters([math.pi / 4, math.pi / 3, math.pi / 2, math.pi / 6])

sim = QuantumSimulator(2)
from_qiskit(bound).run(sim)

print(sim.sv.to_dict())
```

Example 5 - Qiskit circuit with measurement, reading outcomes:

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure(0, 0)
qc.measure(1, 1)

sim = QuantumSimulator(2)
outcomes = from_qiskit(qc).run(sim)
print(outcomes)   # e.g. [0, 0] or [1, 1], always correlated
```

Non-obvious gate name mappings:

| Qiskit name | Local name |
|---|---|
| `cx` | `cnot` |
| `measure` | `mz` |
| `u1` | `p` |
| `u3` / `u` | `u` |
| `tdg` | `tdg` |
| `ccx` | `ccx` |
| `cswap` | `cswap` |

Gates not in the mapping raise `ValueError` with the gate name.

---

## Inspecting simulation state

Three tableau debug formats are available:

```python
# CHP-style: Pauli strings with +/- signs
print(st.format_chp_printstate())

# Raw X and Z bit matrices
print(st.format_xz_binary_matrices())

# Phase column
print(st.format_phase_matrix())

# All three together
print(st.format_tableau_debug())
```

Statevector inspection works through `QuantumSimulator` in either mode:

```python
sv = sim.statevector_snapshot()   # works in either mode
print(sv.data)                    # raw complex128 array, length 2^n
print(sv.probabilities())         # |amplitude|^2 per computational basis state
print(sv.to_dict())               # {bitstring: amplitude} above tolerance
```

---

## Measuring qubits

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

# Measure qubit 0
outcome = st.measure_z(0)
print(f"Outcome: {outcome}")   # 0 or 1, equally likely

# Both qubits are now correlated
print(st.format_chp_printstate())
```

Or measure inline in the circuit:

```python
st = StabilizerState.zero(2)
c = Circuit(2).h(0).cnot(0, 1).mz(0).mz(1)
outcomes = c.run(st)
print(outcomes)   # e.g. [0, 0] or [1, 1]
```

Measurement is implemented in [`StabilizerState.measure_z`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py). The method takes a deterministic path when the measured observable already commutes with the stabilizer group and a random path when the observable anticommutes with a stabilizer generator. The details are in [Measurement](theory/measurement.md).

Measurement also works in statevector mode through `QuantumSimulator.measure_z()` and `.mz()` circuit operations.

---

## Using QEC codes

### 3-qubit bit-flip

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code

# 3 data qubits + 2 ancilla
st = StabilizerState.zero(5)
BitFlip3Code.encoder_circuit().run(st)

# Inject an error
st.x(2)

# Measure syndrome and correct
s01, s12 = BitFlip3Code.measure_syndrome(st)
BitFlip3Code.correct_x_from_syndrome(st, s01, s12)

print(f"Syndrome: ({s01}, {s12})")   # (0, 1) → error was on q2
```

The code lives in [`BitFlip3Code`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py). `measure_syndrome` uses two ancillas to read $Z_0Z_1$ and $Z_1Z_2$, then resets those ancillas to `|0>`.

### Shor 9-qubit code

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import Shor9Code

st = StabilizerState.zero(9)
Shor9Code.encoder_circuit().run(st)

st.x(7)   # inject error

syndrome = Shor9Code.read_syndrome(st)
Shor9Code.correct_x_from_syndrome(st, syndrome)
```

[`Shor9Code`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) builds the 9-qubit encoder and includes a helper for recognizing current single-`X`-error syndrome patterns.

---

## Running the tests

```bash
git clone https://github.com/atharvmunot004/python-stabilizer.git
cd python-stabilizer
pip install -e ".[dev]"
pytest
```

The test suite has 35 tests covering individual gates, Bell/GHZ states, bit-flip code behavior, Shor-code encoding/correction helpers, GF(2) linear algebra, random Clifford circuits, random measurements, Qiskit interoperability checks, and non-Clifford hybrid simulation.

Useful test entry points:

| Test file | Purpose |
|---|---|
| [`tests/test_two_qubit_bell.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_two_qubit_bell.py) | Bell-state preparation and stabilizers |
| [`tests/test_bitflip3.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_bitflip3.py) | 3-qubit repetition-code syndrome and correction |
| [`tests/test_random_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_random_circuits.py) | Tableau invariants under random Clifford and measurement circuits |
| [`tests/test_qiskit_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_qiskit_circuits.py) | Small Qiskit-to-local circuit comparisons |
| [`tests/test_nonclifford_gates.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_nonclifford_gates.py) | Hybrid statevector fallback and non-Clifford gates |

---

## What's next

- [Stabilizer Formalism](theory/stabilizer-formalism.md) - the math behind the simulation
- [Architecture](architecture.md) - hybrid routing and how the modules fit together
- [The Tableau Representation](theory/tableau.md) - how bits map to quantum states
- [Measurement](theory/measurement.md) - deterministic vs random outcomes
- [Error-Correcting Codes](theory/qec-codes.md) - bit-flip and Shor code deep dive
- [Hybrid Simulation](hybrid-simulation.md) - the Clifford/non-Clifford boundary
- [API Reference](api-reference.md) - public classes, gates, and helper functions
