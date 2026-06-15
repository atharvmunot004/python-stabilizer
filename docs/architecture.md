# Architecture

This page is a source-level map of `stabilizer-python`: what each module owns, how data flows through the simulator, and where to look in the GitHub repository when you want to verify or change behavior.

Source links point at the `main` branch of [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer).

---

## Design goals

`stabilizer-python` is intentionally small. The package optimizes for readability and traceability to the stabilizer formalism rather than production-scale simulator throughput.

The main design choices are:

| Goal | Consequence in the code |
|---|---|
| Pure Python runtime | Clifford tableau simulation uses only the standard library; hybrid statevector simulation uses NumPy |
| Explicit tableau representation | State is stored in public bit arrays on `StabilizerState` |
| Theory-to-code readability | Gate, measurement, and statevector rules are written directly instead of hidden behind dense abstractions |
| Small composable API | `StabilizerState` performs Clifford simulation, `QuantumSimulator` routes hybrid simulation, `Circuit` sequences operations, `codes` builds QEC examples |
| Testable invariants | Tests validate stabilizer rank, commutation, round trips, Qiskit interop, and non-Clifford fallback |

---

## Repository layout

| Path | Role |
|---|---|
| [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py) | Public package exports |
| [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) | Core Aaronson-Gottesman tableau state and gate/measurement updates |
| [`stabilizer_python/gate.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/gate.py) | Gate dataclass and full standard gate library |
| [`stabilizer_python/statevector.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/statevector.py) | Dense statevector backend and tableau bridge |
| [`stabilizer_python/simulator.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/simulator.py) | `QuantumSimulator` hybrid router |
| [`stabilizer_python/qiskit_interop.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/qiskit_interop.py) | `from_qiskit()` Qiskit circuit converter |
| [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) | Lightweight fluent circuit builder |
| [`stabilizer_python/tracing.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tracing.py) | `TracedCircuit` wrapper for step-by-step tableau snapshots |
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

The class owns all Clifford state mutation:

- Constructors: [`zero(n)`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py), `from_stabilizer_list(...)`
- Single-qubit Clifford gates: `h`, `s`, `sdg`, `sx`, `sxdg`, `x`, `y`, `z`, `i`
- Two-qubit Clifford gates: `cnot`/`cx`, `cz`, `cy`, `swap`
- Measurement and reset: `measure_z`, `reset_z`
- Validation: `_check_qubit`, `_check_tableau_invariants` (debug/tests)
- Inspection: `inspect`, `stabilizer_generators`, `destabilizer_generators`, `stabilizer_strings`, `destabilizer_strings`, `tableau_dict`, `copy`, `format_chp_printstate`, `format_xz_binary_matrices`, `format_phase_matrix`, `format_tableau_debug`

### `Gate`

[`gate.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/gate.py) defines the `Gate` dataclass:

- `name: str`
- `num_qubits: int`
- `matrix: np.ndarray`, the `2^n x 2^n` unitary
- `is_clifford: bool`
- `params: list[float]`

Fixed gates are module-level instances such as `HGate`, `TGate`, `CXGate`, and `CCXGate`. Parameterized gates are factory functions such as `RZGate(theta)`, `UGate(theta, phi, lam)`, and `RZZGate(theta)`.

Runtime code does not import Qiskit to build matrices. Gate matrices are built from NumPy arrays, Kronecker products, projection operators, and elementary trigonometric formulas.

### `Statevector`

[`statevector.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/statevector.py) owns the dense backend:

- `Statevector(n, data)`: a little-endian `2^n` complex128 array
- `apply_gate(gate, qubits)`: embeds a gate into the full `2^n` space and applies it
- `measure_z(qubit)`: samples and collapses a Z-basis measurement
- `probabilities()`, `to_dict()`, `inner_product()`: inspection helpers
- `tableau_to_statevector(state)`: converts a `StabilizerState` to a `Statevector`

The bridge function applies stabilizer projectors `(I + g_i) / 2` iteratively. It is O(n · 2^n) and is called once at the Clifford-to-non-Clifford boundary.

### `QuantumSimulator`

[`simulator.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/simulator.py) is the routing layer. It holds:

- `mode: str`: `"tableau"` or `"statevector"`
- `tableau: StabilizerState`
- `sv: Statevector | None`

`apply(name, qubits, params)` or `apply_gate(gate, qubits)` routes to `StabilizerState` methods when `is_clifford=True` and `mode == "tableau"`. Otherwise it calls `_switch_to_statevector()` and then `sv.apply_gate()`.

`_switch_to_statevector()` calls `tableau_to_statevector()` exactly once, stores the result, and sets `mode` to `"statevector"`. `measure_z(qubit)` delegates to whichever backend is active. `statevector_snapshot()` returns a dense statevector in either mode without changing `mode`. Pass `trace=True` to record a `SimulatorTraceStep` after every gate with mode before/after and a state snapshot. Pass `debug=True` to assert tableau invariants after Clifford gates and measurements. Gate application validates qubit indices and rejects duplicates before routing.

### `Circuit`

[`Circuit`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) is a minimal operation list. It does not simulate by itself; it records operations and applies them to a `StabilizerState` or `QuantumSimulator` in `run(state)`.

Supported builder operations include Clifford methods (`h`, `s`, `sdg`, `sx`, `sxdg`, `x`, `y`, `z`, `i`, `cnot`, `cx`, `cz`, `cy`, `ch`, `swap`, `iswap`, `cs`, `csdg`, `ecr`, `dcx`), non-Clifford methods (`t`, `tdg`, rotations, controlled rotations, Toffoli, controlled-SWAP), `.gate(g, qubits)`, `.mz(q)`, and `.extend(ops)`.

`Circuit.run(state)` mutates the supplied target and returns measurement outcomes in the order `mz` operations appear.

### `qiskit_interop`

[`qiskit_interop.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/qiskit_interop.py) provides `from_qiskit(qc: QuantumCircuit) -> Circuit`.

It walks `qc.data`, maps each instruction name to the local gate name, extracts qubit indices from the circuit's qubit register, and builds a local `Circuit` using named convenience methods for fixed gates and parameterized builder calls where needed. Barriers and delay instructions are silently skipped. Unknown gate names raise `ValueError`.

Composite Qiskit library instructions are recursively expanded through their definitions when possible. See [How from_qiskit Works](qiskit-interop.md) for the full conversion algorithm.

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

```text
                    Circuit.run(target)
                           |
              +------------+------------+
              |                         |
     target is StabilizerState   target is QuantumSimulator
              |                         |
     pure Clifford path          check gate.is_clifford?
              |                         |
              v                   +-----+------+
    tableau.h / .s / .cnot ...   YES           NO
              |                   |             |
              v                   v             v
       outcomes list       tableau path   _switch_to_statevector()
                           O(n) per gate  tableau_to_statevector()
                                          then sv.apply_gate()
                                          O(2^n) per gate
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

Gate methods on `StabilizerState` update every row of the tableau by Clifford conjugation. This is the Heisenberg-picture view: instead of multiplying a state vector by a unitary, each stabilizer generator is transformed as `g -> U g U†`.

Examples:

- `h(q)` swaps the X and Z bits in column `q`; rows containing `Y` flip sign.
- `s(q)` XORs the X bit into the Z bit in column `q`; rows containing `Y` flip sign.
- `cnot(control, target)` XORs `x[control]` into `x[target]`, XORs `z[target]` into `z[control]`, and applies the Aaronson-Gottesman phase rule.
- Pauli gates (`x`, `y`, `z`) do not change X/Z support; they flip signs of rows that anticommute with the applied Pauli.

Non-Clifford gates (`T`, `Rx`, `Rz`, `U`, `CCX`, and others) carry an explicit `matrix` field on the `Gate` object and are routed to the statevector backend by `QuantumSimulator.apply`. The matrix is a NumPy complex128 array of shape `(2^n, 2^n)` and is applied via `sv.apply_gate(gate, qubits)`, which embeds it into the full Hilbert space using identities on untouched qubits.

The Clifford derivation is in [The Tableau Representation](theory/tableau.md), and the implementation is in [`tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py).

---

## Measurement architecture

`measure_z(q)` has two paths:

1. If no stabilizer row has an X component on `q`, the state is already a Z eigenstate on that qubit. The outcome is deterministic and is computed from existing phase bits.
2. If some stabilizer row has an X component on `q`, the measurement anticommutes with the stabilizer group. The outcome is random, the tableau is row-reduced around a pivot row, and a signed `Z_q` row becomes the new stabilizer.

The random path uses private row operations:

- `_rowmult(a, b)` multiplies Pauli row `a` by row `b`, including phase tracking.
- `_rowswap(a, b)` swaps X, Z, and phase data for two rows.

In statevector mode, `Statevector.measure_z(q)` sums probabilities over basis indices, samples the outcome, zeroes inconsistent amplitudes, and renormalizes.

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
| [`tests/test_nonclifford_gates.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_nonclifford_gates.py) | Statevector fallback and non-Clifford gates |

The most important tableau invariant is that stabilizer rows remain independent and mutually commuting after Clifford gates and measurements. In tests this is checked using the binary symplectic product and `rank_gf2`.

---

## Extension points

The cleanest ways to extend the project are:

- Add a new state-level Clifford gate to `StabilizerState`, then add tests that compare its decomposition or expected stabilizers.
- Add a new gate to `gate.py` as either a module-level instance for fixed gates or a factory function for parameterized gates.
- Set `is_clifford=True` only if the gate maps every Pauli to a single Pauli under conjugation.
- Add a convenience method to `Circuit` and to `QuantumSimulator.apply`'s routing table.
- Add the gate name to `qiskit_interop.py`'s name map if it has a Qiskit equivalent.
- Add new code examples in `codes.py` when the operation is part of a reusable QEC workflow.
- Add examples under [`stabilizer_python/examples/`](https://github.com/atharvmunot004/python-stabilizer/tree/main/stabilizer_python/examples) when the workflow is mainly educational.
- Add docs under `docs/theory/` for math-heavy concepts and under `docs/` for API or architecture guidance.
