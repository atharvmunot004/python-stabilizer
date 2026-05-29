# Getting Started

## Installation

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

With dev dependencies (pytest + Qiskit interop tests):

```bash
pip install "stabilizer-python[dev] @ git+https://github.com/atharvmunot004/python-stabilizer.git"
```

Requirements: Python >= 3.9. No other runtime dependencies.

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

The top half are destabilizers, the bottom half are stabilizer generators. See [The Tableau Representation](theory/tableau.md) for what these mean.

---

## Building circuits

`Circuit` is a fluent gate builder:

```python
from stabilizer_python import StabilizerState, Circuit

# Bell state
st = StabilizerState.zero(2)
c = Circuit(2).h(0).cnot(0, 1)
c.run(st)

print(st.format_chp_printstate())
# +XX
# +ZZ   ← stabilizers of |Φ+>
```

Available gates:

| Method | Gate |
|---|---|
| `.h(q)` | Hadamard |
| `.s(q)` | Phase ($S$) |
| `.x(q)` | Pauli $X$ |
| `.z(q)` | Pauli $Z$ |
| `.cnot(c, t)` | Controlled-NOT |
| `.mz(q)` | Measure Z |

The `run(state)` method returns a list of measurement outcomes (one per `.mz()` call).

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

---

## Inspecting the tableau

Three debug formats are available:

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

---

## Running the tests

```bash
git clone https://github.com/atharvmunot004/python-stabilizer.git
cd python-stabilizer
pip install -e ".[dev]"
pytest
```

The test suite covers: individual gates, Bell/GHZ states, bit-flip code, Shor code, GF(2) linear algebra, random Clifford circuits, and Qiskit interoperability.

---

## What's next

- [Stabilizer Formalism](theory/stabilizer-formalism.md) — the math behind the simulation
- [The Tableau Representation](theory/tableau.md) — how bits map to quantum states
- [Measurement](theory/measurement.md) — deterministic vs random outcomes
- [Error-Correcting Codes](theory/qec-codes.md) — bit-flip and Shor code deep dive
- [API Reference](api-reference.md) — full module documentation
