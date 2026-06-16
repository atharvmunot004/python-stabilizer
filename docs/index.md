# stabilizer-python

A minimal, dependency-free stabilizer (Clifford) simulator in pure Python, built to make the stabilizer formalism readable at the bit level.

The project is both a small simulator and a learning resource. Every operation is close to the underlying Aaronson-Gottesman tableau algorithm: gates update X/Z bit matrices, measurements row-reduce the tableau, and the QEC examples expose syndrome extraction directly.

Source repository: [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer)

---

## What is included

| Component | What it does | Source |
|---|---|---|
| `StabilizerState` | Core Aaronson-Gottesman tableau state representation | [`tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) |
| `Circuit` | Fluent builder for small Clifford circuits | [`circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) |
| `QuantumSimulator` | Hybrid tableau/statevector simulator with optional gate tracing | [`simulator.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/simulator.py) |
| `StabilizerCode` | General `[[n,k,d]]` stabilizer-code class with logicals, syndrome extraction, and distance search | [`stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py) |
| Named codes | `BitFlip3Code`, `PhaseFlip3Code`, `PerfectCode`, `SteaneCode`, `Shor9Code`, `SurfaceCode3` | [`stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py) |
| Legacy QEC helpers | Explicit bit-flip and Shor encoder/syndrome circuits | [`codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) |
| `gaussian_elimination_gf2`, `rank_gf2` | Binary linear algebra helpers | [`linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py) |
| Examples | Runnable Bell, bit-flip, and Shor demos | [`stabilizer_python/examples`](https://github.com/atharvmunot004/python-stabilizer/tree/main/stabilizer_python/examples) |
| Tests | Invariant, random-circuit, QEC, and Qiskit interop checks | [`tests`](https://github.com/atharvmunot004/python-stabilizer/tree/main/tests) |

---

## Capabilities and limits

`stabilizer-python` supports Clifford-state simulation:

- Computational-basis initialization via `StabilizerState.zero(n)`
- Clifford updates: `H`, `S`, Pauli gates, `CNOT`, plus several state-level derived Clifford gates
- Z-basis measurement with deterministic and random tableau update paths
- Small fluent circuits through `Circuit`
- Stabilizer inspection through `inspect()`, `stabilizer_strings()`, `destabilizer_strings()`, and `tableau_dict()`
- Hybrid simulation through `QuantumSimulator`, including optional gate-by-gate tracing
- GF(2) rank and RREF utilities for binary stabilizer checks
- General `StabilizerCode` definitions for small `[[n,k,d]]` codes
- Named code instances for bit-flip, phase-flip, perfect, Steane, Shor, and distance-3 surface-code-style examples
- Educational legacy QEC helpers for explicit bit-flip and Shor circuits

The core tableau simulator is intentionally not a universal quantum simulator. Use `QuantumSimulator` for small circuits that cross into non-Clifford gates such as `T`, rotations, Toffoli, or arbitrary state-vector amplitudes. If you need large-scale production stabilizer simulation, use a tool such as [Stim](https://github.com/quantumlib/Stim); this project is designed to show the mechanics clearly.

---

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

For local development:

```bash
git clone https://github.com/atharvmunot004/python-stabilizer.git
cd python-stabilizer
pip install -e ".[dev]"
```

Runtime requirements are intentionally small: Python `>=3.9` and no required third-party packages. The `dev` extra installs `pytest` and `qiskit` for the optional test suite.

---

## Quick start

### Bell state

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

print(st.inspect(views=["chp"]))
```

Output:

```text
+XI
+IX
---
+XX
+ZZ
```

The stabilizers `+XX` and `+ZZ` are the generators of the Bell state $|\Phi^+\rangle$.

Use `st.inspect()` with no arguments for compact CHP-style output. Pass `views=["chp", "binary", "phase", "debug", "stabilizers", "destabilizers"]` to select specific output.

### 3-qubit bit-flip correction

```python
from stabilizer_python import BitFlip3Code

st = BitFlip3Code.zero_state()

st.x(1)                        # inject an X error on q1
syndrome = BitFlip3Code.read_syndrome(st)
print(syndrome)
# [1, 1]
```

The syndrome `[1, 1]` identifies an `X` error on qubit 1.

---

## Documentation map

- [Getting Started](getting-started/index.md): beginner path for installation, first states, circuits, measurement, Qiskit, QEC, noise, benchmarking, and tests.
- [Architecture](architecture/index.md): module responsibilities, source map, input processing, data flow, measurement internals, and extension points.
- [Stabilizer Formalism](theory/stabilizer-formalism.md): Pauli groups, stabilizers, Clifford evolution, and Gottesman-Knill.
- [The Tableau Representation](theory/tableau.md): how X/Z/phase arrays encode stabilizer states and how gates mutate them.
- [Measurement](theory/measurement.md): deterministic versus random measurement and tableau row updates.
- [Error-Correcting Codes](theory/qec-codes.md): repetition-code and Shor-code concepts mapped to the implementation.
- [General Stabilizer Codes](getting-started/stabilizer-codes.md): creating `[[n,k,d]]` codes from Pauli generators.
- [Noise And Benchmarking](getting-started/benchmarking.md): Pauli noise channels, `EncodedState`, lookup decoders, `benchmark_code`, and threshold scans.
- [Hybrid Simulation](hybrid-simulation.md): how `QuantumSimulator` switches from tableau to statevector mode and records trace snapshots.
- [API Reference](api-reference.md): public classes, functions, method behavior, and source links.
- [References](references.md): papers, tools, textbooks, source resources, and the converted Gottesman-Knill Markdown walkthroughs.
