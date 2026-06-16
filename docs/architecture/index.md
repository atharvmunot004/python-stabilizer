# Architecture Overview

This section is a source-level map of `stabilizer-python`: what each module owns,
how data flows through the simulator, and how inputs are parsed, validated, and
routed through all supported cases.

Source links point at the `main` branch of
[`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer).

---

## Design Goals

`stabilizer-python` is intentionally small. The package optimizes for
readability and traceability to the stabilizer formalism rather than
production-scale simulator throughput.

| Goal | Consequence in the code |
|---|---|
| Pure Python tableau logic | `StabilizerState`, `StabilizerCode`, syndrome extraction, and GF(2) helpers use lists and standard library code |
| Explicit tableau representation | State is stored in public `x_mat`, `z_mat`, and `r_phase` arrays |
| Theory-to-code readability | Gate, measurement, and row-multiplication rules mirror the derivations in the theory docs |
| Hybrid simulation when needed | Clifford operations stay in tableau mode; non-Clifford gates route to `Statevector` through `QuantumSimulator` |
| General QEC definitions | `StabilizerCode` accepts arbitrary `[[n,k,d]]` stabilizer generators as Pauli strings |
| Shot-based QEC benchmarking | Pauli noise helpers, `EncodedState`, and `benchmark_code` provide a small Monte Carlo stack |
| Testable invariants | Tests validate commutation, GF(2) rank, syndrome extraction, logical tracking, noise channels, benchmark loops, Qiskit conversion, and distance checks |

---

## Architecture Pages

Use these pages as a map from user input to implementation behavior:

| Page | What it explains |
|---|---|
| [Module Map](module-map.md) | Every package module, public responsibility, and source link |
| [Input Processing](input-processing.md) | How code processes gate names, qubit indices, Pauli strings, Qiskit instructions, syndrome checks, and invalid cases |
| [Simulation Flow](simulation-flow.md) | How `Circuit`, `QuantumSimulator`, `StabilizerState`, and `Statevector` cooperate |
| [Stabilizer Codes](stabilizer-codes.md) | How `StabilizerCode` validates generators, builds logical zero states, extracts syndromes, computes logicals, and searches distance |
| [Extension Points](extension-points.md) | Where to add gates, backends, code families, docs, and tests |

---

## High-Level Data Flow

```text
User input
   |
   +--> StabilizerState.zero(n)
   |       |
   |       +--> tableau arrays x_mat, z_mat, r_phase
   |
   +--> Circuit(n).h(...).cnot(...).run(target)
   |       |
   |       +--> QuantumSimulator routing or direct tableau mutation
   |
   +--> StabilizerCode(n, k, generators)
   |       |
   |       +--> Pauli-string parsing
   |       +--> commutation/rank validation
   |       +--> logical operators and syndrome checks
   |       +--> EncodedState and benchmark_code workflows
   |
   +--> from_qiskit(qc)
           |
           +--> Qiskit instruction parsing
           +--> local Circuit construction
```

The central invariant is that a valid tableau state keeps its stabilizer rows
independent and mutually commuting. Code-level checks use the binary symplectic
product and GF(2) rank helpers to preserve this invariant.

---

## Source Layout

| Path | Role |
|---|---|
| [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py) | Public package exports |
| [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) | Core Aaronson-Gottesman tableau state and Clifford updates |
| [`stabilizer_python/stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py) | General `[[n,k,d]]` code class and named code instances |
| [`stabilizer_python/encoded_state.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/encoded_state.py) | Logical operator tracking and logical error checks |
| [`stabilizer_python/noise.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/noise.py) | Sampled Pauli noise channels, `NoisyCircuit`, and low-level shot loops |
| [`stabilizer_python/benchmark.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/benchmark.py) | `StabilizerCode`-aware Monte Carlo benchmarking and threshold scans |
| [`stabilizer_python/syndrome.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/syndrome.py) | One-shot and reusable syndrome extraction |
| [`stabilizer_python/ancilla.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/ancilla.py) | Ancilla allocation and mixed Pauli parity checks |
| [`stabilizer_python/gate.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/gate.py) | Gate dataclass, fixed gates, and parameterized gate factories |
| [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) | Fluent operation builder |
| [`stabilizer_python/simulator.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/simulator.py) | Hybrid tableau/statevector router |
| [`stabilizer_python/statevector.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/statevector.py) | Dense non-Clifford backend |
| [`stabilizer_python/qiskit_interop.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/qiskit_interop.py) | Qiskit `QuantumCircuit` conversion |
| [`stabilizer_python/tracing.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tracing.py) | Step-by-step trace snapshots |
| [`stabilizer_python/linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py) | GF(2) RREF and rank |
| [`stabilizer_python/codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) | Legacy pedagogical `BitFlip3Code` and `Shor9Code` helpers |

The top-level package exports the new general-code instances (`BitFlip3Code`,
`PhaseFlip3Code`, `PerfectCode`, `SteaneCode`, `Shor9Code`, `SurfaceCode3`) from
`stabilizer_code.py`. The legacy helpers remain available under
`stabilizer_python.codes`.
