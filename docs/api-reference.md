# API Reference

This page documents the public API exposed by [`stabilizer_python`](https://github.com/atharvmunot004/python-stabilizer/tree/main/stabilizer_python). For a source-level overview, see [Architecture](architecture/index.md).

## `stabilizer_python`

Top-level imports:

```python
from stabilizer_python import (
    StabilizerState,
    Circuit,
    QuantumSimulator,
    StabilizerCode,
    EncodedState,
    SteaneCode,
    PerfectCode,
    BitFlip3Code,
    NoisyCircuit,
    benchmark_code,
    build_lookup_decoder,
    threshold_scan,
    gaussian_elimination_gf2,
    rank_gf2,
    codes,
)
```

Exports are defined in [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py).

---

## `StabilizerState`

Core state representation. An $n$-qubit stabilizer state stored as an Aaronson-Gottesman tableau.

Source: [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)

### Data attributes

`StabilizerState` intentionally keeps its tableau arrays visible for teaching and debugging:

| Attribute | Shape | Meaning |
|---|---|---|
| `n` | scalar | Number of qubits |
| `x_mat` | `2n x n` list of bits | X component of each Pauli row |
| `z_mat` | `2n x n` list of bits | Z component of each Pauli row |
| `r_phase` | `2n` list of bits | Row sign: `0` for `+`, `1` for `-` |

Rows `0..n-1` are destabilizers and rows `n..2n-1` are stabilizer generators.

### Construction

#### `StabilizerState.zero(n: int) -> StabilizerState`

Create the $n$-qubit all-zeros state $|00\cdots0\rangle$.

```python
st = StabilizerState.zero(3)
```

Raises `ValueError` if `n < 1`.

#### `StabilizerState.from_stabilizer_list(stabilizers: List[str]) -> StabilizerState`

Construct a state from signed Pauli stabilizer labels. Each label may start with `+` or `-`; if omitted, `+` is assumed.

```python
st = StabilizerState.from_stabilizer_list(["+XX", "+ZZ"])
print(st.stabilizer_strings())  # ['+XX', '+ZZ']
```

Raises `ValueError` for invalid Pauli characters, inconsistent string lengths, wrong generator count, or identity stabilizer rows.

---

### Gates

All gate methods modify the state in place and return `None`.

#### `h(q: int)` - Hadamard
#### `s(q: int)` - Phase gate $S$
#### `sdg(q: int)` / `s_dagger(q: int)` - $S^\dagger$
#### `sx(q: int)` / `sqrt_x(q: int)` - $\sqrt{X}$
#### `sxdg(q: int)` / `sqrt_x_dagger(q: int)` - $\sqrt{X}^\dagger$
#### `x(q: int)` - Pauli $X$
#### `y(q: int)` - Pauli $Y$
#### `z(q: int)` - Pauli $Z$
#### `i(q: int)` - Identity (no-op)
#### `cnot(control: int, target: int)` / `cx(control, target)` - Controlled-NOT
#### `cz(control: int, target: int)` - Controlled-Z
#### `cy(control: int, target: int)` - Controlled-Y
#### `swap(q1: int, q2: int)` - SWAP (via 3 CNOTs)

All gate and measurement methods validate qubit indices and raise `ValueError`
if a target is out of range for the state's `n` qubits.

#### `_check_tableau_invariants() -> None`

Debug helper. Asserts that stabilizer rows are independent and mutually
commuting. Intended for tests and for `QuantumSimulator(debug=True)`.

---

### Measurement

#### `measure_z(q: int) -> int`

Measure qubit `q` in the Z basis. Returns `0` (eigenvalue $+1$) or `1` (eigenvalue $-1$).

- If the outcome is **deterministic**, computes it from the tableau phases with no randomness.
- If the outcome is **random**, samples uniformly and updates the tableau to the post-measurement state.

```python
outcome = st.measure_z(0)
```

#### `reset_z(q: int) -> int`

Measure qubit `q` and apply $X$ if the outcome was 1, leaving qubit `q` in $|0\rangle$. Returns the measurement outcome.

```python
m = st.reset_z(ancilla)   # ancilla is now |0> regardless
```

---

### Inspection

#### `stabilizer_generators() -> List[Tuple[int, List[int], List[int]]]`

Returns the $n$ stabilizer generators as a list of `(phase_bit, x_row, z_row)` tuples.

- `phase_bit`: 0 for $+1$, 1 for $-1$
- `x_row`: list of $n$ bits, `x_row[q]` is 1 if the Pauli has $X$ or $Y$ on qubit $q$
- `z_row`: list of $n$ bits, `z_row[q]` is 1 if the Pauli has $Z$ or $Y$ on qubit $q$

```python
for phase, x, z in st.stabilizer_generators():
    print(phase, x, z)
```

#### `stabilizer_strings() -> List[str]`

Returns the $n$ stabilizer generators as signed Pauli strings.

```python
st = StabilizerState.from_stabilizer_list(["XX", "ZZ"])
print(st.stabilizer_strings())  # ['+XX', '+ZZ']
```

This mirrors Qiskit's `Clifford.to_labels(mode="S")` style. See [Comparison with Qiskit's Clifford](theory/tableau.md#comparison-with-qiskits-clifford) for layout differences.

#### `destabilizer_strings() -> List[str]`

Returns the $n$ destabilizer generators as signed Pauli strings.

```python
st = StabilizerState.zero(2)
print(st.destabilizer_strings())  # ['+XI', '+IX']
```

This mirrors Qiskit's `Clifford.to_labels(mode="D")` style. Destabilizers are tableau bookkeeping rows used for efficient measurement simulation, not the physical stabilizer generators of the state.

#### `destabilizer_generators() -> List[Tuple[int, List[int], List[int]]]`

Returns the first $n$ tableau rows as `(phase_bit, x_row, z_row)` tuples. Symmetric with `stabilizer_generators()`.

#### `tableau_dict() -> Dict[str, List[str]]`

Returns both generator sets as signed Pauli strings:

```python
st = StabilizerState.zero(2)
print(st.tableau_dict())
# {'stabilizers': ['+ZI', '+IZ'], 'destabilizers': ['+XI', '+IX']}
```

#### `copy() -> StabilizerState`

Returns a deep copy of the state.

The copied state has independent `x_mat`, `z_mat`, and `r_phase` lists.

---

### Debug formatting

#### `inspect(views: Optional[List[str]] = None) -> str`

Unified tableau inspection entrypoint. Returns formatted text; it does not print by itself.

```python
print(st.inspect())  # default: same as views=["chp"]
```

When `views` is `None`, `inspect()` returns the `chp` view only.

Request multiple views explicitly:

```python
print(st.inspect(views=["chp", "binary", "phase", "debug"]))
```

When `views` is a list, only those views are returned, in the order requested:

```python
print(st.inspect(views=["stabilizers", "destabilizers"]))
print(st.inspect(views=["chp", "binary", "phase"]))
```

Supported view names:

| View | Output |
|---|---|
| `chp` | CHP-style destabilizer rows, separator, and stabilizer rows |
| `binary` | Raw X and Z bit matrices |
| `phase` | Phase-bit column |
| `debug` | CHP rows plus X/Z matrices plus phase column |
| `stabilizers` | Stabilizer rows only (`n..2n-1`) as signed Pauli strings |
| `destabilizers` | Destabilizer rows only (`0..n-1`) as signed Pauli strings |

Raises `ValueError` if any requested view name is unknown.

#### `format_chp_printstate() -> str`

CHP-style output: destabilizer rows, a separator line, stabilizer rows. Each row prefixed with `+` or `-`.

```
+XI
+IX
-----------
+XX
+ZZ
```

#### `format_xz_binary_matrices() -> str`

Prints the raw $2n \times n$ X and Z bit tables side by side.

#### `format_phase_matrix() -> str`

Prints the $2n \times 1$ phase bit column.

#### `format_tableau_debug() -> str`

All three formats combined. Useful for step-by-step debugging.

Equivalent to the `debug` view in `inspect()`.

Formatting methods are for inspection only. They use `io.StringIO` internally
and should not be called inside tight simulation loops. For bulk runs, prefer
`stabilizer_strings()` or raw measurement outcomes over repeated CHP formatting.

---

## `Circuit`

Lightweight fluent circuit builder.

Source: [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py)

### `Circuit(n_qubits: int)`

```python
c = Circuit(3)
```

### Gate methods

All return `self` for chaining.

| Method | Gate |
|---|---|
| `.h(q)` | Hadamard |
| `.s(q)` | Phase |
| `.sdg(q)` | S dagger |
| `.sx(q)` / `.sxdg(q)` | Square-root X and inverse |
| `.x(q)` | Pauli X |
| `.y(q)` | Pauli Y |
| `.z(q)` | Pauli Z |
| `.i(q)` | Identity |
| `.cnot(control, target)` / `.cx(control, target)` | CNOT |
| `.cz(control, target)` / `.cy(control, target)` / `.ch(control, target)` | Controlled Clifford gates |
| `.swap(q1, q2)` / `.iswap(q1, q2)` | Swap-style gates |
| `.t(q)` / `.tdg(q)` | T and T dagger |
| `.rx(theta, q)` / `.ry(theta, q)` / `.rz(theta, q)` | Single-qubit rotations |
| `.p(lam, q)` / `.u(theta, phi, lam, q)` | Phase and U gates |
| `.crz(theta, control, target)` | Controlled rotation |
| `.rxx(theta, q1, q2)` / `.rzz(theta, q1, q2)` | Two-qubit rotations |
| `.ccx(c1, c2, target)` | Toffoli |
| `.cswap(control, target1, target2)` | Controlled-SWAP |
| `.gate(g, qubits)` | Generic `Gate` object |
| `.mz(q, key=None)` | Measure Z |
| `.extend(ops)` | Append a list of `Op` objects |

`Circuit` can be run on either a `StabilizerState` for Clifford circuits or a `QuantumSimulator` for hybrid circuits.

### `run(state: StabilizerState | QuantumSimulator) -> List[int]`

Apply all ops to `state`. Returns list of measurement outcomes (one per `.mz()` call), in order.

```python
st = StabilizerState.zero(2)
outcomes = Circuit(2).h(0).cnot(0, 1).mz(0).mz(1).run(st)
```

### `Op`

Frozen dataclass: `Op(name: str, targets: Tuple[int, ...])`. Gate name is a string like `"H"`, `"CNOT"`, `"MZ"`, `"MZ:key"`.

`key` in `.mz(q, key="name")` is stored in the op name for readability, but `Circuit.run` currently returns outcomes as an ordered list rather than a key-value mapping.

---

## `StabilizerCode`

General `[[n,k,d]]` stabilizer-code abstraction.

Source: [`stabilizer_python/stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py)

### Constructor

#### `StabilizerCode(n, k, generators, name="", logical_xs=None, logical_zs=None)`

Create a stabilizer code from `n-k` independent, mutually commuting Pauli
generators.

```python
from stabilizer_python import StabilizerCode

code = StabilizerCode(
    n=3,
    k=1,
    generators=["+ZZI", "+IZZ"],
    name="Bit-flip [[3,1,1]]",
    logical_xs=["+XXX"],
    logical_zs=["+IIZ"],
)
```

Arguments:

| Argument | Type | Meaning |
|---|---|---|
| `n` | `int` | number of physical qubits |
| `k` | `int` | number of logical qubits |
| `generators` | `List[str]` | signed or unsigned Pauli strings, exactly `n-k` entries |
| `name` | `str` | optional human-readable label |
| `logical_xs` | `Optional[List[str]]` | optional logical X operators, exactly `k` entries |
| `logical_zs` | `Optional[List[str]]` | optional logical Z operators, exactly `k` entries |

Validation:

- `n >= 1`
- `0 <= k <= n`
- `len(generators) == n-k`
- every generator has length `n`
- every generator uses only `I`, `X`, `Y`, `Z`, with optional `+` or `-`
- generators have GF(2) rank `n-k`
- generators commute pairwise under the binary symplectic product
- provided logical operators commute with stabilizers, are not stabilizers, and
  have the correct logical anticommutation relations

Raises `ValueError` for invalid definitions.

### Attributes

| Attribute | Type | Meaning |
|---|---|---|
| `n` | `int` | physical qubits |
| `k` | `int` | logical qubits |
| `generators` | `List[str]` | normalized signed generators |
| `name` | `str` | display name |

### `zero_state() -> StabilizerState`

Return the logical $|0_L\rangle$ codeword.

```python
from stabilizer_python import SteaneCode

state = SteaneCode.zero_state()
print(SteaneCode.read_syndrome(state))
# [0, 0, 0, 0, 0, 0]
```

The state is built from the stabilizer checks plus one logical `+Z_L` per
logical qubit.

### `StabilizerCode.zero_logical(code) -> StabilizerState`

Compatibility classmethod:

```python
state = StabilizerCode.zero_logical(SteaneCode)
```

Equivalent to `SteaneCode.zero_state()`.

### `encode(state: StabilizerState) -> None`

Mutate an existing `StabilizerState` into the logical zero codeword.

```python
from stabilizer_python import StabilizerState, PerfectCode

state = StabilizerState.zero(5)
PerfectCode.encode(state)
```

Raises `ValueError` if `state.n != code.n`.

### `encoding_circuit() -> Circuit`

Return a best-effort Clifford encoder circuit for simple CSS/repetition-style
codes.

The authoritative preparation path is `zero_state()`, because it directly
constructs the target stabilizer state. `encoding_circuit()` is primarily a
pedagogical helper.

### `read_syndrome(state: StabilizerState) -> List[int]`

Extract all syndrome bits for the code generators.

```python
from stabilizer_python import BitFlip3Code

state = BitFlip3Code.zero_state()
state.x(1)
print(BitFlip3Code.read_syndrome(state))
# [1, 1]
```

The method:

1. checks that `state.n == code.n`
2. strips signs from generators
3. delegates to `syndrome.read_syndrome`
4. adds/removes a temporary ancilla internally

### `syndrome_extractor(state: StabilizerState) -> SyndromeExtractor`

Return a reusable extractor for repeated syndrome rounds.

```python
state = BitFlip3Code.zero_state()
extractor = BitFlip3Code.syndrome_extractor(state)
print(extractor.extract())
```

Unlike `read_syndrome`, this keeps an ancilla attached to the state.

### `logical_x(logical_qubit=0) -> str`

Return the logical X operator for a logical qubit.

```python
print(PerfectCode.logical_x())
# +XXXXX
```

Raises `IndexError` if `logical_qubit` is outside `0..k-1`.

### `logical_z(logical_qubit=0) -> str`

Return the logical Z operator for a logical qubit.

```python
print(PerfectCode.logical_z())
# +ZZZZZ
```

Raises `IndexError` if `logical_qubit` is outside `0..k-1`.

### `distance() -> int`

Compute the minimum weight of a non-trivial logical operator.

```python
print(PerfectCode.distance())  # 3
print(SteaneCode.distance())   # 3
```

The implementation performs an exact minimum-weight search over normalizer
operators for small codes. It is exponential and intended for educational-size
codes.

### Named Code Instances

Top-level exports:

| Name | Parameters | Description |
|---|---|---|
| `BitFlip3Code` | `[[3,1,1]]` | bit-flip repetition code |
| `PhaseFlip3Code` | `[[3,1,1]]` | phase-flip repetition code |
| `PerfectCode` | `[[5,1,3]]` | 5-qubit perfect code |
| `SteaneCode` | `[[7,1,3]]` | Steane CSS code |
| `Shor9Code` | `[[9,1,3]]` | Shor-code stabilizer instance |
| `SurfaceCode3` | `[[9,1,3]]` | distance-3 surface-code-style instance |

For a tutorial, see [General Stabilizer Codes](getting-started/stabilizer-codes.md).
For internal validation details, see
[Architecture: Stabilizer Codes](architecture/stabilizer-codes.md).

---

## `EncodedState`

Logical-operator wrapper around a physical `StabilizerState`.

Source: [`stabilizer_python/encoded_state.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/encoded_state.py)

Constructor: `EncodedState(state: StabilizerState, code, *, code_name: str = "")`

The wrapper reads logical operators from `code.logical_x(i)` and
`code.logical_z(i)`, keeps a small logical frame, and compares observed logical
signs against that frame when checking for residual errors.

```python
from stabilizer_python import BitFlip3Code, EncodedState

state = BitFlip3Code.zero_state()
encoded = EncodedState(state, BitFlip3Code)

print(encoded.logical_z_eigenvalue())  # +1
print(encoded.logical_state_string())  # |0_L>
```

### Construction helpers

#### `EncodedState.from_logical_ops(state, logical_xs, logical_zs, check_operators=None, code_name="")`

Construct directly from logical Pauli strings when a full `StabilizerCode`
object is not available.

### Logical readout

#### `logical_z_eigenvalue(logical_qubit: int = 0) -> Optional[int]`
#### `logical_x_eigenvalue(logical_qubit: int = 0) -> Optional[int]`

Return `+1`, `-1`, or `None` when the observable is not determined by the
current stabilizer group.

#### `measure_logical_z(logical_qubit: int = 0) -> int`
#### `measure_logical_x(logical_qubit: int = 0) -> int`

Return classical bits: `0` for eigenvalue `+1`, `1` for eigenvalue `-1`.
These are non-destructive logical readouts; they do not measure physical qubits.

### Logical error checks

#### `has_logical_x_error(logical_qubit: int = 0) -> bool`
#### `has_logical_z_error(logical_qubit: int = 0) -> bool`
#### `has_logical_error() -> bool`
#### `logical_error_type(logical_qubit: int = 0) -> str`

`logical_error_type()` returns `"I"`, `"X"`, `"Z"`, or `"Y"`.

### Code membership and logical gates

#### `syndrome() -> List[int]`
#### `is_valid_codeword() -> bool`
#### `apply_logical_x(logical_qubit: int = 0) -> None`
#### `apply_logical_z(logical_qubit: int = 0) -> None`
#### `apply_logical_y(logical_qubit: int = 0) -> None`
#### `apply_logical_h(logical_qubit: int = 0) -> None`
#### `logical_state_string(logical_qubit: int = 0) -> str`
#### `summary() -> str`

Apply intentional logical Pauli gates through `EncodedState`, not directly to
the physical tableau, when you want the logical frame updated.

---

## `noise`

Single-shot Pauli noise channels for Monte Carlo simulation.

Source: [`stabilizer_python/noise.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/noise.py)

These functions mutate a `StabilizerState` in place and return which sampled
Pauli error was applied.

### Single-qubit channels

#### `apply_pauli_channel(state, qubit, p_x, p_y, p_z) -> str`
#### `apply_depolarizing(state, qubit, p) -> str`
#### `apply_bit_flip(state, qubit, p) -> str`
#### `apply_phase_flip(state, qubit, p) -> str`
#### `apply_bit_phase_flip(state, qubit, p) -> str`

Returned value is one of `"I"`, `"X"`, `"Y"`, or `"Z"`.
Probabilities must be in `[0, 1]`; custom Pauli channels must satisfy
`p_x + p_y + p_z <= 1`.

### Multi-qubit helpers

#### `apply_pauli_channel_all(state, p_x, p_y, p_z, qubits=None) -> List[str]`
#### `apply_depolarizing_all(state, p, qubits=None) -> List[str]`
#### `apply_bit_flip_all(state, p, qubits=None) -> List[str]`
#### `apply_phase_flip_all(state, p, qubits=None) -> List[str]`

Each target qubit is sampled independently. If `qubits` is omitted, all qubits
in the state are targeted.

### `NoisyCircuit`

`NoisyCircuit(n: int, gate_error: float = 0.0, meas_error: float = 0.0)`

Subclass of `Circuit` that injects depolarizing noise after Clifford gates and
flips returned measurement bits with probability `meas_error`.

```python
from stabilizer_python import NoisyCircuit, StabilizerState

state = StabilizerState.zero(2)
outcomes = NoisyCircuit(2, gate_error=0.01).h(0).cnot(0, 1).mz(0).run(state)
```

With a `StabilizerState`, `NoisyCircuit` supports Clifford operations. Run
non-Clifford circuits on `QuantumSimulator`.

### `run_shots(...) -> dict`

Low-level shot loop retained from E2:

```python
run_shots(
    encode_fn,
    check_operators,
    decoder_fn,
    noise_channel,
    n_shots,
    n_data,
    logical_x=None,
    logical_z=None,
    seed=None,
)
```

Use `benchmark_code()` for the newer `StabilizerCode`-integrated E4 workflow.

---

## `benchmark`

Shot-based syndrome sampling for decoder evaluation.

Source: [`stabilizer_python/benchmark.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/benchmark.py)

### Dataclasses

#### `ShotRecord`

Per-shot details:

| Field | Meaning |
|---|---|
| `shot_index` | zero-based shot number |
| `syndrome` | measured syndrome bits |
| `correction` | decoder output as `(qubit, pauli)` pairs |
| `logical_error_type` | `"I"`, `"X"`, `"Z"`, or `"Y"` |
| `had_logical_error` | whether any logical error remained |

#### `CodeBenchmarkResult`

Aggregated result from `benchmark_code()`. Main fields include `n_shots`,
`n_logical_errors`, `logical_error_rate`, `n_x_errors`, `n_z_errors`,
`x_error_rate`, `z_error_rate`, `elapsed_seconds`, `shots_per_second`, `seed`,
and optional `records`.

Methods:

- `summary() -> str`

#### `ThresholdScanResult`

Result from `threshold_scan()`. Stores the physical `p_values`, logical/X/Z
rates, `n_shots_per_p`, `code_name`, and the full per-point benchmark results.

Methods:

- `as_dict() -> Dict[float, float]`
- `summary() -> str`

### Benchmark functions

#### `benchmark_code(code, noise_model, decoder, n_shots, *, seed=None, record_shots=False, verbose=False) -> CodeBenchmarkResult`

Each shot constructs a fresh `StabilizerState.zero(code.n)`, calls
`code.encode(state)`, applies `noise_model(state)`, extracts
`code.read_syndrome(state)`, applies decoder corrections, and checks residual
logical errors through `EncodedState`.

```python
from stabilizer_python import BitFlip3Code, benchmark_code, build_lookup_decoder
from stabilizer_python.noise import apply_bit_flip_all

decoder = build_lookup_decoder(BitFlip3Code)
result = benchmark_code(
    BitFlip3Code,
    noise_model=lambda st: apply_bit_flip_all(st, p=0.05, qubits=[0, 1, 2]),
    decoder=decoder,
    n_shots=500,
    seed=42,
)
```

#### `threshold_scan(code, noise_model_factory, decoder, p_values, n_shots_per_p, *, seed=None, verbose=True) -> ThresholdScanResult`

Runs `benchmark_code()` once for each physical error rate. The factory receives
`p` and returns a `noise_model`.

#### `compare_codes(codes, noise_model_factory, decoder_factory, p_values, n_shots_per_p, *, seed=None, verbose=True) -> Dict[str, ThresholdScanResult]`

Convenience wrapper for running the same scan over several codes.

#### `build_lookup_decoder(code, noise_model_factory=None, *, max_errors=1) -> Callable`

Enumerates Pauli errors up to `max_errors`, computes their syndromes, and
returns a minimum-weight lookup decoder. Intended for small codes.

For a tutorial, see [Noise And Benchmarking](getting-started/benchmarking.md).

---

## `codes` Legacy Helpers

Source: [`stabilizer_python/codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py)

### `BitFlip3Code`

3-qubit repetition code for single $X$-error correction. All methods are `@staticmethod`.

#### `encoder_circuit() -> Circuit`

Returns the encoding circuit for 3 qubits (input on q0, ancillas q1/q2 as $|0\rangle$).

#### `syndrome_circuit() -> Circuit`

Returns a syndrome measurement circuit for 5 qubits (3 data + 2 ancilla). Uses `.mz()` ops with keys `"s01"` and `"s12"`.

#### `measure_syndrome(state, *, ancilla_01=3, ancilla_12=4) -> Tuple[int, int]`

Directly measures $Z_0Z_1$ and $Z_1Z_2$ into ancilla qubits and resets them. Returns `(s01, s12)`.

#### `correct_x_from_syndrome(state, s01: int, s12: int) -> None`

Applies the corrective $X$ gate based on syndrome:

| $(s_{01}, s_{12})$ | Error location |
|:---:|:---:|
| $(0, 0)$ | No error |
| $(1, 0)$ | Qubit 0 |
| $(1, 1)$ | Qubit 1 |
| $(0, 1)$ | Qubit 2 |

#### `read_syndrome(state) -> Tuple[int, int]`

Reads syndrome from stabilizer phases directly (no ancilla required, no measurement collapse).

This helper expects the relevant data-qubit stabilizers to be present in the state's generator set. If the state is not in the expected encoded layout, it raises `ValueError`.

---

### `Shor9Code`

9-qubit Shor-code encoder and syndrome helpers. All methods are `@staticmethod`.

The current implementation provides the encoder and an `X`-error syndrome correction helper. Full phase-error correction is explained in [Error-Correcting Codes](theory/qec-codes.md), but is not yet exposed as a separate helper.

#### `encoder_circuit() -> Circuit`

Returns the 9-qubit encoding circuit (input on q0, all others $|0\rangle$).

#### `read_syndrome(state) -> Tuple[int, ...]`

Returns tuple of 9 phase bits from all stabilizer generators.

#### `correct_x_from_syndrome(state, syndrome: Tuple[int, ...]) -> None`

Applies $X$ on the qubit matching the syndrome pattern, if recognized.

If the syndrome does not match a stored single-`X` pattern, the method leaves the state unchanged.

---

### Convenience functions

#### `run_2qubit_bell() -> Tuple[StabilizerState, List[int]]`

Returns a `StabilizerState` prepared in the Bell state $|\Phi^+\rangle$ on 2 qubits.

#### `bitflip3_encode_zero_state() -> StabilizerState`

Returns a `StabilizerState` with $|0_L\rangle$ encoded in the 3-qubit bit-flip code.

---

## `linear_algebra`

GF(2) linear algebra utilities.

Source: [`stabilizer_python/linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py)

### `gaussian_elimination_gf2(matrix) -> Tuple[List[List[int]], List[int]]`

Compute reduced row-echelon form (RREF) of a binary matrix over GF(2).

- Input: rectangular list-of-lists with entries in `{0, 1}`
- Returns: `(rref_matrix, pivot_columns)`
- Input is not modified

```python
from stabilizer_python import gaussian_elimination_gf2

M = [[1, 0, 1], [1, 1, 0], [0, 1, 1]]
rref, pivots = gaussian_elimination_gf2(M)
```

### `rank_gf2(matrix) -> int`

Returns the rank of a binary matrix over GF(2).

```python
from stabilizer_python import rank_gf2

rank = rank_gf2([[1, 0, 1], [1, 1, 0], [0, 1, 1]])
# -> 3
```

---

## `Gate`

Source: `stabilizer_python/gate.py`

The `Gate` dataclass represents a quantum gate as a data object.

Fields:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Gate identifier string, such as `"h"`, `"rz"`, or `"ccx"` |
| `num_qubits` | `int` | Number of qubits the gate acts on |
| `matrix` | `np.ndarray` | Unitary matrix of shape `(2**num_qubits, 2**num_qubits)`, dtype `complex128` |
| `is_clifford` | `bool` | True if the gate maps every Pauli to a single Pauli under conjugation |
| `params` | `list[float]` | Parameter values; empty list for fixed gates |

Fixed single-qubit Clifford gate instances:

`IGate`, `HGate`, `XGate`, `YGate`, `ZGate`, `SGate`, `SdgGate`, `SXGate`, `SXdgGate`

Fixed single-qubit non-Clifford gate instances:

`TGate`, `TdgGate`

Fixed two-qubit Clifford gate instances:

`CXGate`, `CNOTGate`, `CYGate`, `CZGate`, `CHGate`, `SwapGate`, `iSwapGate`, `ECRGate`, `DCXGate`, `CSGate`, `CSdgGate`

Fixed three-qubit gate instances:

`CCXGate`, `ToffoliGate`, `CCZGate`, `CSwapGate`, `FredkinGate`, `MCXGate`

Parameterized gate factories:

`RXGate(theta)`, `RYGate(theta)`, `RZGate(theta)`, `PhaseGate(lam)`, `U1Gate(lam)`, `U2Gate(phi, lam)`, `U3Gate(theta, phi, lam)`, `UGate(theta, phi, lam)`, `RGate(theta, phi)`, `CRXGate(theta)`, `CRYGate(theta)`, `CRZGate(theta)`, `CPhaseGate(lam)`, `RXXGate(theta)`, `RYYGate(theta)`, `RZZGate(theta)`, `RZXGate(theta)`, `XXPlusYYGate(theta, beta)`, `XXMinusYYGate(theta, beta)`

Example:

```python
from stabilizer_python import TGate, RZGate
import math

print(TGate.matrix)
print(RZGate(math.pi / 4).matrix)
```

---

## `Statevector`

Source: `stabilizer_python/statevector.py`

Dense little-endian statevector for n-qubit systems.

Constructor: `Statevector(n: int, data: np.ndarray | None = None)`

- `n`: number of qubits
- `data`: optional length-`2**n` complex128 array; if omitted initializes to $|0...0\rangle$

Methods:

#### `apply_gate(gate: Gate, qubits: list[int]) -> None`

Embed `gate.matrix` into the full `2^n` Hilbert space and apply it. Qubit ordering follows the Qiskit/little-endian convention: qubit 0 is the least significant bit in the computational basis index.

#### `measure_z(qubit: int) -> int`

Measure qubit in the Z basis. Collapses the statevector in place. Returns 0 or 1.

#### `probabilities() -> np.ndarray`

Returns a length-`2**n` array of `|amplitude|^2` values.

#### `to_dict(tol: float = 1e-10) -> dict[str, complex]`

Returns `{bitstring: amplitude}` for all amplitudes with absolute value above `tol`. Bitstring ordering: qubit 0 is the rightmost character.

#### `inner_product(other: Statevector) -> complex`

Computes `<self|other>`.

Module-level function:

#### `tableau_to_statevector(state: StabilizerState) -> Statevector`

Converts a stabilizer tableau to the unique statevector it represents. Algorithm: applies the projector `(I + g_i) / 2` for each stabilizer generator `g_i` to an initial state, then renormalizes. Cost: O(n · 2^n). It is called once at the Clifford-to-non-Clifford boundary inside `QuantumSimulator`.

Example:

```python
from stabilizer_python import StabilizerState, Circuit
from stabilizer_python.statevector import tableau_to_statevector

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

sv = tableau_to_statevector(st)
print(sv.to_dict())
# {'00': (0.707+0j), '11': (0.707+0j)}
```

---

## `QuantumSimulator`

Source: `stabilizer_python/simulator.py`

Hybrid simulator. Starts in O(n²) tableau mode; auto-switches to O(2^n) statevector on the first non-Clifford gate.

Constructor: `QuantumSimulator(n: int, trace: bool = False, debug: bool = False)`

Attributes:

| Attribute | Type | Description |
|---|---|---|
| `mode` | `str` | `"tableau"` or `"statevector"` |
| `tableau` | `StabilizerState` | Active in tableau mode |
| `sv` | `Statevector \| None` | Active after first non-Clifford gate |
| `n` | `int` | Number of qubits |
| `trace` | `List[SimulatorTraceStep]` | Gate-by-gate snapshots when `trace=True` |

Pass `debug=True` to run tableau invariant checks after every Clifford gate and
Z measurement while the simulator is in tableau mode. Out-of-range or duplicate
qubit indices raise `ValueError` before a gate is applied.

Methods:

#### `apply(name: str, qubits: list[int], params: list[float] | None = None) -> None`

Apply a gate by name. Clifford gates route to the tableau; non-Clifford gates trigger the statevector switch. Gate name must match a key in the internal routing table, using the same strings as `gate.py` `Gate.name` values.

#### `apply_gate(gate: Gate, qubits: list[int]) -> None`

Apply a `Gate` object directly. Routes by `gate.is_clifford`.

#### `measure_z(qubit: int) -> int`

Measure in the Z basis. Delegates to the active backend.

#### `reset(qubit: int) -> None`

Measure and apply X if outcome was 1, restoring $|0\rangle$.

#### `statevector_snapshot() -> Statevector`

Return the current state as a `Statevector` without modifying `mode`. In tableau mode this calls `tableau_to_statevector`.

Example:

```python
from stabilizer_python import QuantumSimulator
import math

sim = QuantumSimulator(2)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
print(sim.mode)   # "tableau"

sim.apply("rz", [0], params=[math.pi / 4])
print(sim.mode)   # "statevector"

print(sim.sv.to_dict())
```

#### Gate tracing

Pass `trace=True` to record the state after every `apply` / `apply_gate` call:

```python
from stabilizer_python import QuantumSimulator
import math

sim = QuantumSimulator(3, trace=True)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("rz", [0], params=[math.pi / 4])

for step in sim.trace:
    print(step.gate_name, step.qubits, step.mode_after)
    if step.mode_after == "tableau":
        print(step.snapshot.format_chp_printstate())
    else:
        print(step.snapshot.to_dict())
```

Each `SimulatorTraceStep` captures: gate name, qubit targets, params, mode before and after, and a snapshot (`StabilizerState.copy()` or `Statevector` copy).

---

## `tracing`

Source: [`stabilizer_python/tracing.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tracing.py)

Step-by-step Clifford circuit tracing for QEC pedagogy.

### `TraceStep`

Frozen dataclass recorded for each traced operation:

| Field | Type | Meaning |
|---|---|---|
| `index` | `int` | 1-based step number |
| `op_label` | `str` | Formatted gate or measurement label |
| `kind` | `str` | `"gate"` or `"measurement"` |
| `state` | `StabilizerState` | Tableau snapshot after the operation |
| `outcome` | `Optional[int]` | Measurement outcome for `MZ` steps |
| `measurement_branch` | `Optional[str]` | `"deterministic"` or `"random"` for `MZ` steps |

### `SimulatorTraceStep`

Frozen dataclass recorded for each traced gate in `QuantumSimulator(trace=True)`:

| Field | Type | Meaning |
|---|---|---|
| `gate_name` | `str` | Gate name, e.g. `"h"`, `"cnot"`, `"rz"` |
| `qubits` | `List[int]` | Target qubit indices |
| `params` | `List[float]` | Gate parameters (empty for fixed gates) |
| `mode_before` | `str` | `"tableau"` or `"statevector"` before the gate |
| `mode_after` | `str` | Mode after the gate |
| `snapshot` | `StabilizerState \| Statevector` | State copy after the gate |

### `TracedCircuit`

#### `TracedCircuit(circuit: Circuit, trace: bool = True)`

Wrap a `Circuit` for optional step recording.

#### `run(state: StabilizerState) -> List[int]`

Apply the wrapped circuit to `state` in place. Returns measurement outcomes in circuit order. When `trace=True`, appends a `TraceStep` after every gate and measurement.

Raises `ValueError` if the state has fewer qubits than the circuit, or if a non-Clifford operation forces the simulator out of tableau mode.

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tracing import TracedCircuit

st = StabilizerState.zero(5)
BitFlip3Code.encoder_circuit().run(st)

tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
outcomes = tc.run(st)
tc.print_trace()
```

#### `print_trace() -> None`

Print every recorded step: operation label, measurement outcome and branch when applicable, and CHP-style tableau output.

#### `steps: List[TraceStep]`

Programmatic access to recorded steps after `run()`.

---

## `qiskit_interop`

Source: `stabilizer_python/qiskit_interop.py`

Qiskit integration. Requires `qiskit` to be installed separately:

```bash
pip install qiskit
```

#### `from_qiskit(qc: qiskit.circuit.QuantumCircuit) -> Circuit`

Converts a Qiskit `QuantumCircuit` into a local `Circuit`. The returned `Circuit` can be run on either a `StabilizerState` for Clifford circuits or a `QuantumSimulator`.

See [How from_qiskit Works](qiskit-interop.md) for the full conversion walkthrough.

- Parameterized gates are translated using bound numeric parameters. If the circuit contains unbound `ParameterExpression` objects, a `ValueError` is raised.
- `barrier` and `delay` instructions are silently skipped.
- Unknown gate names raise `ValueError` with the gate name so they are easy to add.
- Qubit indices are taken from the circuit's flat qubit list in order.

Gate name mapping:

| Qiskit | Local |
|---|---|
| `cx` | `cnot` |
| `measure` | `mz` |
| `u1` | `p` |
| `u3` | `u` |
| `tdg` | `tdg` |
| `ccx` | `ccx` |
| `cswap` | `cswap` |
| all others | same name |

Example:

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.t(2)
qc.ccx(0, 1, 2)

sim = QuantumSimulator(3)
from_qiskit(qc).run(sim)

print(sim.mode)           # "statevector"
print(sim.sv.probabilities())
```
