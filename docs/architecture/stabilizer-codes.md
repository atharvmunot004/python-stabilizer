# Stabilizer Code Architecture

`StabilizerCode` is the general `[[n,k,d]]` code layer. It replaces hardcoded
code definitions for new workflows while keeping the older `codes.py` helpers
available for backwards compatibility.

Source:
[`stabilizer_python/stabilizer_code.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/stabilizer_code.py)

---

## What A Code Object Stores

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

Attributes:

| Attribute | Meaning |
|---|---|
| `n` | number of physical qubits |
| `k` | number of logical qubits |
| `generators` | normalized signed stabilizer generator strings |
| `name` | human-readable label |
| `_logical_xs` | optional cached/provided logical X operators |
| `_logical_zs` | optional cached/provided logical Z operators |
| `_distance` | cached computed distance |

The constructor expects exactly `n-k` independent, mutually commuting
stabilizer generators.

---

## Parsing And Normalization

The helper `_parse_pauli(s)` converts each signed Pauli string to:

```text
(phase_bit, x_row, z_row)
```

Example:

```text
+XZZXI
phase_bit = 0
x_row     = [1, 0, 0, 1, 0]
z_row     = [0, 1, 1, 1, 0]
```

The mapping is:

| Pauli | X bit | Z bit |
|---|---:|---:|
| `I` | 0 | 0 |
| `X` | 1 | 0 |
| `Y` | 1 | 1 |
| `Z` | 0 | 1 |

`StabilizerCode` stores a normalized signed string. If the user omits a sign,
the code stores `+`.

---

## Generator Validation

`_validate_generators()` checks two properties.

### Independence

Each generator becomes a binary vector `[x | z]`. The list of vectors must have
GF(2) rank `n-k`.

If two generators are duplicates or one is a product of the others, the rank is
too small and construction raises `ValueError`.

### Commutation

Two Pauli strings commute iff their binary symplectic product is zero:

$$
\sum_q x_i[q] z_j[q] + z_i[q] x_j[q] \pmod 2 = 0
$$

If any pair anticommutes, construction raises `ValueError` and includes the
offending generator indices in the message.

---

## Logical Operator Validation

If `logical_xs` and `logical_zs` are provided, they are validated immediately.

For each logical operator:

1. It must have length `n`.
2. It must not be identity.
3. It must commute with every stabilizer generator.
4. It must not lie in the stabilizer span.

For every logical pair:

1. `logical_x(i)` must anticommute with `logical_z(i)`.
2. `logical_x(i)` must commute with `logical_x(j)`.
3. `logical_z(i)` must commute with `logical_z(j)`.
4. `logical_x(i)` must commute with `logical_z(j)` when `i != j`.

If logicals are not provided, the class computes them lazily from the
symplectic complement.

---

## Logical Zero State Construction

`zero_state()` constructs the logical $|0_L\rangle$ state.

Algorithm:

1. Start with the `n-k` stabilizer checks.
2. Append `+Z_L` for every logical qubit.
3. Pass the resulting `n` commuting generators to
   `StabilizerState.from_stabilizer_list(...)`.

This is why clean code states have zero syndrome:

```python
from stabilizer_python import SteaneCode

state = SteaneCode.zero_state()
print(SteaneCode.read_syndrome(state))
# [0, 0, 0, 0, 0, 0]
```

`encode(state)` mutates an existing `StabilizerState` by copying the logical
zero tableau into it. It requires `state.n == code.n`.

---

## Syndrome Extraction

`read_syndrome(state)` is a one-shot helper.

```text
StabilizerCode.read_syndrome(state)
   |
   +--> verify state.n == code.n
   +--> strip signs from generators
   +--> syndrome.read_syndrome(state, checks)
          |
          +--> add one |0> ancilla
          +--> for each check: mixed_parity_check(...)
          +--> remove ancilla in finally block
```

Returned bits follow the stabilizer convention:

| Bit | Meaning |
|---:|---|
| `0` | check measured eigenvalue `+1` |
| `1` | check measured eigenvalue `-1` |

`syndrome_extractor(state)` returns a reusable `SyndromeExtractor`. It keeps an
ancilla attached to the state and is better for repeated rounds.

---

## EncodedState Logical Tracking

`EncodedState` lives one layer above `StabilizerCode`.

```text
EncodedState(state, code)
   |
   +--> read code.logical_x(i) and code.logical_z(i)
   +--> store check operators from code.generators
   +--> read current logical eigenvalues as the expected frame
```

It is used for two related jobs:

1. Non-destructive logical readout, such as `logical_z_eigenvalue()`.
2. Residual logical error classification after noise and decoder correction.

When a logical gate is intentional, callers should apply it through
`EncodedState.apply_logical_x()`, `apply_logical_z()`, or `apply_logical_y()` so
the expected logical frame changes with the physical state.

---

## Shot-Based Benchmark Flow

`benchmark_code()` is the E4 code-level Monte Carlo loop.

```text
benchmark_code(code, noise_model, decoder, n_shots)
   |
   +--> for each shot:
          |
          +--> state = StabilizerState.zero(code.n)
          +--> code.encode(state)
          +--> noise_model(state)
          +--> syndrome = code.read_syndrome(state)
          +--> correction = decoder(syndrome)
          +--> apply correction Pauli gates
          +--> enc = EncodedState(state, code)
          +--> classify residual logical X/Z/Y errors
```

The loop intentionally allocates a fresh tableau per shot. Noise and syndrome
extraction mutate the state in place, so reusing a pre-encoded state would leak
state between shots.

`threshold_scan()` repeats that loop for each physical error rate and stores one
`CodeBenchmarkResult` per point. `build_lookup_decoder()` constructs a small
minimum-weight decoder by enumerating Pauli errors and their syndromes.

---

## Logical Operator Computation

When logicals are not supplied, `_compute_logical_operators()` computes them.

High-level algorithm:

1. Convert stabilizer generators to `[x | z]` vectors.
2. Build a commutation constraint matrix. A candidate vector `v = [x | z]`
   commutes with generator `h = [h_x | h_z]` iff `[h_z | h_x] · v = 0`.
3. Compute a GF(2) nullspace basis of the constraint matrix. This is the
   normalizer candidate space.
4. Remove stabilizer-span directions to get representatives of `N(S)/S`.
5. Pair vectors with symplectic product 1 to form logical X/Z pairs.
6. Convert vectors back to signed Pauli strings.

For named codes, logical operators are supplied explicitly so the public output
is stable and easy to read.

---

## Distance Computation

`distance()` returns the minimum weight of a non-trivial logical operator.

The implementation performs a minimum-weight normalizer search:

1. Enumerate Pauli supports by increasing weight.
2. For each support, enumerate all `X/Y/Z` assignments.
3. Keep candidates that commute with every stabilizer generator.
4. Reject candidates in the stabilizer span.
5. Return the first weight that survives.

This is exhaustive and exact for the small named codes included in the package.
It is intentionally not optimized for large codes.

Examples:

```python
from stabilizer_python import PerfectCode, SteaneCode

print(PerfectCode.distance())  # 3
print(SteaneCode.distance())   # 3
```

---

## Named Code Instances

| Name | Parameters | Generators | Logical X | Logical Z |
|---|---|---:|---|---|
| `BitFlip3Code` | `[[3,1,1]]` | 2 | `+XXX` | `+IIZ` |
| `PhaseFlip3Code` | `[[3,1,1]]` | 2 | `+IIX` | `+ZZZ` |
| `PerfectCode` | `[[5,1,3]]` | 4 | `+XXXXX` | `+ZZZZZ` |
| `SteaneCode` | `[[7,1,3]]` | 6 | `+XXXXXXX` | `+ZZZZZZZ` |
| `Shor9Code` | `[[9,1,3]]` | 8 | `+XXXXXXXXX` | `+ZIIZIIZII` |
| `SurfaceCode3` | `[[9,1,3]]` | 8 | `+XXXIIIIII` | `+ZIIZIIZII` |

The Shor generators match the stabilizers produced by the existing legacy
`codes.Shor9Code.encoder_circuit()` path.

---

## Current Limitations

- `encoding_circuit()` is a simple best-effort helper for CSS/repetition-style
  encoders. The authoritative preparation path is `zero_state()`.
- Distance search is exact but exponential in `n`; it is intended for small
  educational codes.
- `build_lookup_decoder()` provides a small exhaustive decoder for low-weight
  errors, but it is not a scalable decoder for large codes.
- The older `codes.py` classes remain useful for explicit pedagogical circuits.
