# Architecture

This page is a source-level map of `stabilizer-python`: what each module owns, how data flows through the simulator, and where to look in the GitHub repository when you want to verify or change behavior.

Source links point at the `main` branch of [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer).

---

## Design goals

`stabilizer-python` is intentionally small. The package optimizes for readability and traceability to the stabilizer formalism rather than production-scale simulator throughput.

The main design choices are:

| Goal | Consequence in the code |
|---|---|
| Pure Python runtime | No runtime dependencies beyond the standard library |
| Explicit tableau representation | State is stored in public bit arrays on `StabilizerState` |
| Theory-to-code readability | Gate and measurement rules are written directly instead of hidden behind dense linear algebra abstractions |
| Small composable API | `StabilizerState` performs simulation, `Circuit` sequences operations, `codes` builds QEC examples |
| Testable invariants | Tests validate stabilizer rank, commutation, round trips, and selected Qiskit interop cases |

---

## Repository layout

| Path | Role |
|---|---|
| [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py) | Public package exports |
| [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) | Core Aaronson-Gottesman tableau state and gate/measurement updates |
| [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) | Lightweight fluent circuit builder |
| [`stabilizer_python/codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) | Bit-flip and Shor-code examples plus convenience helpers |
| [`stabilizer_python/linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py) | GF(2) RREF and rank utilities |
| [`stabilizer_python/examples/`](https://github.com/atharvmunot004/python-stabilizer/tree/main/stabilizer_python/examples) | Runnable examples for Bell, bit-flip, and Shor code workflows |
| [`tests/`](https://github.com/atharvmunot004/python-stabilizer/tree/main/tests) | Unit and integration-style tests |
| [`docs/`](https://github.com/atharvmunot004/python-stabilizer/tree/main/docs) | This MkDocs documentation site |
| [`mkdocs.yml`](https://github.com/atharvmunot004/python-stabilizer/blob/main/mkdocs.yml) | Documentation site configuration |
| [`pyproject.toml`](https://github.com/atharvmunot004/python-stabilizer/blob/main/pyproject.toml) | Build metadata, package discovery, and dev dependencies |

---

## Runtime components

### `StabilizerState`

[`StabilizerState`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) is the simulator core. It stores an `n`-qubit state as:

- `x_mat`: a `2n x n` binary matrix for X components of Pauli rows
- `z_mat`: a `2n x n` binary matrix for Z components of Pauli rows
- `r_phase`: a `2n`-bit sign vector, where `0` means `+` and `1` means `-`
- `n`: the number of qubits

Rows `0..n-1` are destabilizers. Rows `n..2n-1` are stabilizer generators. This follows Aaronson-Gottesman's extended tableau representation and makes measurement efficient.

The class owns all state mutation:

- Constructors: [`zero(n)`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)
- Single-qubit Clifford gates: `h`, `s`, `sdg`, `sx`, `sxdg`, `x`, `y`, `z`, `i`
- Two-qubit Clifford gates: `cnot`/`cx`, `cz`, `cy`, `swap`
- Measurement and reset: `measure_z`, `reset_z`
- Inspection: `stabilizer_generators`, `copy`, `format_chp_printstate`, `format_xz_binary_matrices`, `format_phase_matrix`, `format_tableau_debug`

### `Circuit`

[`Circuit`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) is a minimal operation list. It does not simulate by itself; it records operations and applies them to a `StabilizerState` in `run(state)`.

Supported circuit-builder operations are:

- `h(q)`
- `s(q)`
- `x(q)`
- `z(q)`
- `cnot(control, target)`
- `mz(q, key=None)`
- `extend(ops)`

`Circuit.run(state)` mutates the supplied state and returns measurement outcomes in the order `mz` operations appear.

### `codes`

[`codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) contains pedagogical QEC workflows built on top of `Circuit` and `StabilizerState`.

`BitFlip3Code` implements:

- `encoder_circuit()`
- `syndrome_circuit()`
- `measure_syndrome(state, ancilla_01=3, ancilla_12=4)`
- `read_syndrome(state)`
- `correct_x_from_syndrome(state, s01, s12)`

`Shor9Code` implements:

- `encoder_circuit()`
- `read_syndrome(state)`
- `correct_x_from_syndrome(state, syndrome)`

The Shor encoder constructs the 9-qubit code state. The current correction helper recognizes and corrects single-qubit `X` errors from stored syndrome patterns; the theory page explains the full Shor-code idea, including phase protection.

### `linear_algebra`

[`linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py) provides small GF(2) helpers:

- `gaussian_elimination_gf2(matrix)` returns an RREF copy and pivot columns
- `rank_gf2(matrix)` returns the binary rank

The tests use these helpers to validate stabilizer independence and tableau invariants.

---

## Simulation flow

The usual data flow is:

```text
StabilizerState.zero(n)
        |
        v
Circuit(...).h(...).cnot(...).mz(...)
        |
        v
Circuit.run(state)
        |
        +--> state.h / state.s / state.cnot / ...
        |
        +--> state.measure_z(...) -> measurement bits
        |
        v
Mutated StabilizerState + list[int] outcomes
```

For code examples, `codes.py` builds circuits or directly manipulates the state:

```text
BitFlip3Code.encoder_circuit()
        |
        v
Circuit.run(state)
        |
        v
BitFlip3Code.measure_syndrome(state)
        |
        +--> state.cnot(data, ancilla)
        +--> state.measure_z(ancilla)
        +--> state.reset_z(ancilla)
        |
        v
BitFlip3Code.correct_x_from_syndrome(...)
```

---

## Gate architecture

Gate methods update every row of the tableau by Clifford conjugation. This is the Heisenberg-picture view: instead of multiplying a state vector by a unitary, each stabilizer generator is transformed as `g -> U g U†`.

Examples:

- `h(q)` swaps the X and Z bits in column `q`; rows containing `Y` flip sign.
- `s(q)` XORs the X bit into the Z bit in column `q`; rows containing `Y` flip sign.
- `cnot(control, target)` XORs `x[control]` into `x[target]`, XORs `z[target]` into `z[control]`, and applies the Aaronson-Gottesman phase rule.
- Pauli gates (`x`, `y`, `z`) do not change X/Z support; they flip signs of rows that anticommute with the applied Pauli.

The full derivation is in [The Tableau Representation](theory/tableau.md), and the implementation is in [`tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py).

---

## Measurement architecture

`measure_z(q)` has two paths:

1. If no stabilizer row has an X component on `q`, the state is already a Z eigenstate on that qubit. The outcome is deterministic and is computed from existing phase bits.
2. If some stabilizer row has an X component on `q`, the measurement anticommutes with the stabilizer group. The outcome is random, the tableau is row-reduced around a pivot row, and a signed `Z_q` row becomes the new stabilizer.

The random path uses private row operations:

- `_rowmult(a, b)` multiplies Pauli row `a` by row `b`, including phase tracking.
- `_rowswap(a, b)` swaps X, Z, and phase data for two rows.

This is the most delicate part of the simulator; see [Measurement](theory/measurement.md) for the algorithmic explanation and [`test_random_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_random_circuits.py) for invariant checks.

---

## Testing strategy

The test suite is intentionally close to simulator invariants:

| Test file | What it covers |
|---|---|
| [`tests/test_two_qubit_bell.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_two_qubit_bell.py) | Bell-state stabilizers and formatting |
| [`tests/test_bitflip3.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_bitflip3.py) | 3-qubit repetition-code encode, syndrome, correction |
| [`tests/test_gaussian_elimination.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_gaussian_elimination.py) | GF(2) RREF and rank |
| [`tests/test_additional_clifford_gates.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_additional_clifford_gates.py) | Extra state-level Clifford operations |
| [`tests/test_random_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_random_circuits.py) | Random Clifford round trips, measurement validity, commutation, rank |
| [`tests/test_qiskit_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_qiskit_circuits.py) | Small Qiskit-to-local conversion checks |

The most important invariant is that stabilizer rows remain independent and mutually commuting after gates and measurements. In tests this is checked using the binary symplectic product and `rank_gf2`.

---

## Extension points

The cleanest ways to extend the project are:

- Add a new state-level Clifford gate to `StabilizerState`, then add tests that compare its decomposition or expected stabilizers.
- Add a matching fluent method to `Circuit` only if circuits need to record that operation.
- Add new code examples in `codes.py` when the operation is part of a reusable QEC workflow.
- Add examples under [`stabilizer_python/examples/`](https://github.com/atharvmunot004/python-stabilizer/tree/main/stabilizer_python/examples) when the workflow is mainly educational.
- Add docs under `docs/theory/` for math-heavy concepts and under `docs/` for API or architecture guidance.

For non-Clifford gates such as `T`, this tableau architecture is not enough by itself. Supporting universal simulation would require a different representation or a stabilizer-rank/decomposition approach.
