# Module Map

This page describes each source module, the public surface it owns, and the
implementation boundary it should maintain.

---

## Public Exports

[`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py)
collects the package's top-level imports. Users can import the common API from
`stabilizer_python` directly:

```python
from stabilizer_python import (
    StabilizerState,
    Circuit,
    QuantumSimulator,
    StabilizerCode,
    SteaneCode,
    PerfectCode,
    BitFlip3Code,
)
```

The same file also exports gates, GF(2) helpers, syndrome tools, magic-state
helpers, noise helpers, logical-state wrappers, benchmark helpers, and the
`codes` submodule.

---

## Core Tableau State

[`tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)
defines `StabilizerState`.

It owns:

- tableau storage: `x_mat`, `z_mat`, `r_phase`, and `n`
- constructors: `zero(n)` and `from_stabilizer_list(stabilizers)`
- Clifford gates: `h`, `s`, `sdg`, `sx`, `sxdg`, `x`, `y`, `z`, `i`, `cnot`, `cx`, `cz`, `cy`, `swap`
- measurement/reset: `measure_z(q)` and `reset_z(q)`
- ancilla lifecycle: `add_ancilla_zero()`, `add_ancilla_plus()`, `remove_ancilla(q)`
- inspection: `stabilizer_strings()`, `destabilizer_strings()`, `tableau_dict()`, `inspect(...)`
- invariant checks: `_check_qubit(...)` and `_check_tableau_invariants()`

Rows `0..n-1` are destabilizers. Rows `n..2n-1` are stabilizers. Every gate
method updates all `2n` rows by Clifford conjugation.

---

## General Stabilizer Codes

[`stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py)
defines the new `StabilizerCode` abstraction.

It owns:

- parsing signed Pauli strings into binary X/Z rows
- validating `[[n,k]]` generator count, length, characters, independence, and commutation
- constructing logical `|0_L>` states from checks plus logical Z operators
- one-shot syndrome extraction via `read_syndrome(state)`
- reusable syndrome extraction via `syndrome_extractor(state)`
- logical operator lookup or computation
- distance search by minimum-weight normalizer element
- named code instances:
  - `BitFlip3Code`
  - `PhaseFlip3Code`
  - `PerfectCode`
  - `SteaneCode`
  - `Shor9Code`
  - `SurfaceCode3`

The new top-level names intentionally shadow the older `codes.py` classes at
`from stabilizer_python import BitFlip3Code`. The old helper classes remain
available as `stabilizer_python.codes.BitFlip3Code` and
`stabilizer_python.codes.Shor9Code`.

---

## Logical State Tracking

[`encoded_state.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/encoded_state.py)
defines `EncodedState`.

It owns:

- binding a physical `StabilizerState` to a code's logical X/Z operators
- non-destructive logical X/Z eigenvalue readout
- logical state labels such as `|0_L>` and `|+_L>`
- residual logical X/Z/Y error checks
- syndrome and codeword-validity checks using the code stabilizers
- logical Pauli operations that update a tracked logical frame

`benchmark.py` constructs `EncodedState` after decoder correction to classify
residual logical errors shot by shot.

---

## Noise and Benchmarking

[`noise.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/noise.py)
defines sampled Pauli noise helpers:

- `apply_pauli_channel`
- `apply_depolarizing`
- `apply_bit_flip`
- `apply_phase_flip`
- `apply_bit_phase_flip`
- the corresponding `_all` helpers for independent multi-qubit sampling
- `NoisyCircuit`
- the low-level `run_shots(...)` helper

[`benchmark.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/benchmark.py)
defines the `StabilizerCode`-aware Monte Carlo layer:

- `ShotRecord`
- `CodeBenchmarkResult`
- `ThresholdScanResult`
- `benchmark_code`
- `threshold_scan`
- `compare_codes`
- `build_lookup_decoder`

The split is intentional: `noise.py` owns sampled physical errors and circuit
noise, while `benchmark.py` owns code-level decoder evaluation.

---

## Legacy Code Examples

[`codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py)
contains older pedagogical helpers:

- `codes.BitFlip3Code.encoder_circuit()`
- `codes.BitFlip3Code.syndrome_circuit()`
- `codes.BitFlip3Code.measure_syndrome(...)`
- `codes.BitFlip3Code.correct_x_from_syndrome(...)`
- `codes.Shor9Code.encoder_circuit()`
- `codes.Shor9Code.correct_x_from_syndrome(...)`

These classes are retained for backwards compatibility and for explicit circuit
walkthroughs. New code definitions should prefer `StabilizerCode`.

---

## Syndrome and Ancilla Modules

[`syndrome.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/syndrome.py)
defines:

- `read_syndrome(state, check_operators)`
- `SyndromeExtractor(state, check_operators, n_ancillas=1)`

[`ancilla.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/ancilla.py)
defines:

- `x_parity_check`
- `y_parity_check`
- `z_parity_check`
- `mixed_parity_check`
- `AncillaRegister`

`StabilizerCode.read_syndrome()` delegates to `syndrome.read_syndrome()` after
stripping generator signs.

---

## Circuit, Gate, and Simulator Layers

[`gate.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/gate.py)
defines `Gate` objects. Every gate carries a name, arity, matrix, Clifford flag,
and parameter list.

[`circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py)
records operations as `Op` objects and applies them in order with `run(state)`.

[`simulator.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/simulator.py)
owns `QuantumSimulator`, which starts in tableau mode and switches to
statevector mode on the first non-Clifford gate.

[`statevector.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/statevector.py)
owns dense non-Clifford evolution.

---

## Interop, Tracing, and Linear Algebra

[`qiskit_interop.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/qiskit_interop.py)
converts Qiskit `QuantumCircuit` objects into local `Circuit` objects.

[`tracing.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tracing.py)
records step-by-step tableau snapshots for pedagogical debugging.

[`linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py)
provides `gaussian_elimination_gf2` and `rank_gf2`. `stabilizer_code.py` also
contains internal pure-Python helpers for row reduction and nullspace extraction
where it needs a slightly different shape of result.
