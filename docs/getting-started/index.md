# Getting Started

This section is a beginner-friendly path through `stabilizer-python`. It starts with installation and a first tableau state, then builds up to circuits, measurement, non-Clifford gates, Qiskit interop, QEC examples, general stabilizer codes, noise, benchmarking, and tests.

If you are new to stabilizer simulation, read these pages in order:

| Step | Page | What you learn |
|---|---|---|
| 1 | [Installation](installation.md) | How to install the package and optional dev tools |
| 2 | [Your First Tableau State](first-tableau.md) | What `StabilizerState.zero()` creates and how to read the output |
| 3 | [Building Circuits](circuits.md) | How to build and run Clifford circuits with `Circuit` |
| 4 | [Inspecting Tableaux](inspection.md) | How to print every tableau view with `inspect()` |
| 5 | [Measuring Qubits](measurement.md) | How Z-basis measurement works from user code |
| 6 | [Hybrid Simulation](non-clifford.md) | When to use `QuantumSimulator` for non-Clifford gates |
| 7 | [Qiskit Interop](qiskit.md) | How to load Qiskit circuits into the local simulator ([internals](../qiskit-interop.md)) |
| 8 | [QEC Examples](qec.md) | How to run general-code and legacy bit-flip/Shor workflows |
| 9 | [General Stabilizer Codes](stabilizer-codes.md) | How to define `[[n,k,d]]` codes from Pauli generators |
| 10 | [Noise And Benchmarking](benchmarking.md) | How to sample Pauli noise, track logical errors, and run threshold scans |
| 11 | [Tracing Syndrome Extraction](tracing.md) | Step-by-step tableau evolution during syndrome measurement |
| 12 | [Running Tests](tests.md) | How to validate a checkout and find useful test examples |

## Which Simulator Should I Use?

| If your circuit contains... | Use |
|---|---|
| Only Clifford gates and Z measurements | `StabilizerState` directly |
| QEC encoders, syndrome extraction, tableau debugging | `StabilizerCode` plus `StabilizerState` |
| Shot-based decoder benchmarks | `benchmark_code`, Pauli noise helpers, and `EncodedState` |
| `T`, rotations, Toffoli, or arbitrary unitary gates | `QuantumSimulator` |
| Qiskit circuits with unknown gate mix | `QuantumSimulator` |

The short version: use `StabilizerState` while the circuit is purely Clifford. Use `QuantumSimulator` when the circuit may cross into non-Clifford gates.

## Minimal Example

```python
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

print(st.inspect(views=["stabilizers"]))
```

Output:

```text
+XX
+ZZ
```

Those two stabilizers identify the Bell state $|\Phi^+\rangle$.

## Deeper References

After this section, continue with:

- [Stabilizer Formalism](../theory/stabilizer-formalism.md) for the math
- [The Tableau Representation](../theory/tableau.md) for the bit-level storage
- [Measurement](../theory/measurement.md) for deterministic and random measurement paths
- [Architecture](../architecture/index.md) for module-level design and input-processing details
- [API Reference](../api-reference.md) for method-level details
