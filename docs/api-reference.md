# API Reference

## `stabilizer_python`

Top-level imports:

```python
from stabilizer_python import StabilizerState, Circuit, gaussian_elimination_gf2, rank_gf2, codes
```

---

## `StabilizerState`

Core state representation. An $n$-qubit stabilizer state stored as an Aaronson–Gottesman tableau.

### Construction

#### `StabilizerState.zero(n: int) → StabilizerState`

Create the $n$-qubit all-zeros state $|00\cdots0\rangle$.

```python
st = StabilizerState.zero(3)
```

Raises `ValueError` if `n < 1`.

---

### Gates

All gate methods modify the state in place and return `None`.

#### `h(q: int)` — Hadamard
#### `s(q: int)` — Phase gate $S$
#### `sdg(q: int)` / `s_dagger(q: int)` — $S^\dagger$
#### `sx(q: int)` / `sqrt_x(q: int)` — $\sqrt{X}$
#### `sxdg(q: int)` / `sqrt_x_dagger(q: int)` — $\sqrt{X}^\dagger$
#### `x(q: int)` — Pauli $X$
#### `y(q: int)` — Pauli $Y$
#### `z(q: int)` — Pauli $Z$
#### `i(q: int)` — Identity (no-op)
#### `cnot(control: int, target: int)` / `cx(control, target)` — Controlled-NOT
#### `cz(control: int, target: int)` — Controlled-Z
#### `cy(control: int, target: int)` — Controlled-Y
#### `swap(q1: int, q2: int)` — SWAP (via 3 CNOTs)

---

### Measurement

#### `measure_z(q: int) → int`

Measure qubit `q` in the Z basis. Returns `0` (eigenvalue $+1$) or `1` (eigenvalue $-1$).

- If the outcome is **deterministic**, computes it from the tableau phases with no randomness.
- If the outcome is **random**, samples uniformly and updates the tableau to the post-measurement state.

```python
outcome = st.measure_z(0)
```

#### `reset_z(q: int) → int`

Measure qubit `q` and apply $X$ if the outcome was 1, leaving qubit `q` in $|0\rangle$. Returns the measurement outcome.

```python
m = st.reset_z(ancilla)   # ancilla is now |0> regardless
```

---

### Inspection

#### `stabilizer_generators() → List[Tuple[int, List[int], List[int]]]`

Returns the $n$ stabilizer generators as a list of `(phase_bit, x_row, z_row)` tuples.

- `phase_bit`: 0 for $+1$, 1 for $-1$
- `x_row`: list of $n$ bits, `x_row[q]` is 1 if the Pauli has $X$ or $Y$ on qubit $q`
- `z_row`: list of $n$ bits, `z_row[q]` is 1 if the Pauli has $Z$ or $Y$ on qubit $q`

```python
for phase, x, z in st.stabilizer_generators():
    print(phase, x, z)
```

#### `copy() → StabilizerState`

Returns a deep copy of the state.

---

### Debug formatting

#### `format_chp_printstate() → str`

CHP-style output: destabilizer rows, a separator line, stabilizer rows. Each row prefixed with `+` or `-`.

```
+XI
+IX
-----------
+XX
+ZZ
```

#### `format_xz_binary_matrices() → str`

Prints the raw $2n \times n$ X and Z bit tables side by side.

#### `format_phase_matrix() → str`

Prints the $2n \times 1$ phase bit column.

#### `format_tableau_debug() → str`

All three formats combined. Useful for step-by-step debugging.

---

## `Circuit`

Lightweight fluent circuit builder.

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
| `.x(q)` | Pauli X |
| `.z(q)` | Pauli Z |
| `.cnot(control, target)` | CNOT |
| `.mz(q, key=None)` | Measure Z |
| `.extend(ops)` | Append a list of `Op` objects |

### `run(state: StabilizerState) → List[int]`

Apply all ops to `state`. Returns list of measurement outcomes (one per `.mz()` call), in order.

```python
st = StabilizerState.zero(2)
outcomes = Circuit(2).h(0).cnot(0, 1).mz(0).mz(1).run(st)
```

### `Op`

Frozen dataclass: `Op(name: str, targets: Tuple[int, ...])`. Gate name is a string like `"H"`, `"CNOT"`, `"MZ"`, `"MZ:key"`.

---

## `codes`

### `BitFlip3Code`

3-qubit repetition code for single $X$-error correction. All methods are `@staticmethod`.

#### `encoder_circuit() → Circuit`

Returns the encoding circuit for 3 qubits (input on q0, ancillas q1/q2 as $|0\rangle$).

#### `syndrome_circuit() → Circuit`

Returns a syndrome measurement circuit for 5 qubits (3 data + 2 ancilla). Uses `.mz()` ops with keys `"s01"` and `"s12"`.

#### `measure_syndrome(state, *, ancilla_01=3, ancilla_12=4) → Tuple[int, int]`

Directly measures $Z_0Z_1$ and $Z_1Z_2$ into ancilla qubits and resets them. Returns `(s01, s12)`.

#### `correct_x_from_syndrome(state, s01: int, s12: int) → None`

Applies the corrective $X$ gate based on syndrome:

| $(s_{01}, s_{12})$ | Error location |
|:---:|:---:|
| $(0, 0)$ | No error |
| $(1, 0)$ | Qubit 0 |
| $(1, 1)$ | Qubit 1 |
| $(0, 1)$ | Qubit 2 |

#### `read_syndrome(state) → Tuple[int, int]`

Reads syndrome from stabilizer phases directly (no ancilla required, no measurement collapse).

---

### `Shor9Code`

9-qubit Shor code correcting any single-qubit error. All methods are `@staticmethod`.

#### `encoder_circuit() → Circuit`

Returns the 9-qubit encoding circuit (input on q0, all others $|0\rangle$).

#### `read_syndrome(state) → Tuple[int, ...]`

Returns tuple of 9 phase bits from all stabilizer generators.

#### `correct_x_from_syndrome(state, syndrome: Tuple[int, ...]) → None`

Applies $X$ on the qubit matching the syndrome pattern, if recognized.

---

### Convenience functions

#### `run_2qubit_bell() → Tuple[StabilizerState, List[int]]`

Returns a `StabilizerState` prepared in the Bell state $|\Phi^+\rangle$ on 2 qubits.

#### `bitflip3_encode_zero_state() → StabilizerState`

Returns a `StabilizerState` with $|0_L\rangle$ encoded in the 3-qubit bit-flip code.

---

## `linear_algebra`

GF(2) linear algebra utilities.

### `gaussian_elimination_gf2(matrix) → Tuple[List[List[int]], List[int]]`

Compute reduced row-echelon form (RREF) of a binary matrix over GF(2).

- Input: rectangular list-of-lists with entries in `{0, 1}`
- Returns: `(rref_matrix, pivot_columns)`
- Input is not modified

```python
from stabilizer_python import gaussian_elimination_gf2

M = [[1, 0, 1], [1, 1, 0], [0, 1, 1]]
rref, pivots = gaussian_elimination_gf2(M)
```

### `rank_gf2(matrix) → int`

Returns the rank of a binary matrix over GF(2).

```python
from stabilizer_python import rank_gf2

rank = rank_gf2([[1, 0, 1], [1, 1, 0], [0, 1, 1]])
# → 3
```
