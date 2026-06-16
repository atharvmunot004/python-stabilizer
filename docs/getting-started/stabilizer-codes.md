# General Stabilizer Codes

`StabilizerCode` lets you define a quantum error-correcting code from stabilizer
generators instead of using a hardcoded class. It supports arbitrary small
`[[n,k,d]]` stabilizer codes written as Pauli strings.

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

---

## Named Codes

The package includes named code instances:

```python
from stabilizer_python import (
    BitFlip3Code,
    PhaseFlip3Code,
    PerfectCode,
    SteaneCode,
    Shor9Code,
    SurfaceCode3,
)
```

| Code | Parameters | Purpose |
|---|---|---|
| `BitFlip3Code` | `[[3,1,1]]` | repetition code for single X-error detection/correction examples |
| `PhaseFlip3Code` | `[[3,1,1]]` | phase-flip repetition code |
| `PerfectCode` | `[[5,1,3]]` | smallest perfect single-error-correcting stabilizer code |
| `SteaneCode` | `[[7,1,3]]` | CSS code from the Hamming code |
| `Shor9Code` | `[[9,1,3]]` | Shor code stabilizer instance |
| `SurfaceCode3` | `[[9,1,3]]` | distance-3 surface-code-style stabilizer instance |

The older circuit helpers remain available as `stabilizer_python.codes`.

---

## Logical State Wrapper

Use `EncodedState` when you want logical observables and logical error checks on
top of a physical `StabilizerState`.

```python
from stabilizer_python import BitFlip3Code, EncodedState

state = BitFlip3Code.zero_state()
encoded = EncodedState(state, BitFlip3Code)

print(encoded.logical_state_string())  # |0_L>
print(encoded.is_valid_codeword())     # True

state.x(0)
print(encoded.syndrome())              # [1, 0]
print(encoded.logical_error_type())    # I for a detectable single-qubit error
```

`EncodedState` is also the logical-error checker used by `benchmark_code()`.

---

## Prepare A Logical Zero State

Use `zero_state()` to prepare $|0_L\rangle$:

```python
from stabilizer_python import SteaneCode

state = SteaneCode.zero_state()
print(state.stabilizer_strings())
```

Internally, this constructs a full stabilizer state from:

- the code's stabilizer checks
- one logical `+Z_L` operator per logical qubit

For a clean codeword, the syndrome is all zeros:

```python
syndrome = SteaneCode.read_syndrome(state)
print(syndrome)
# [0, 0, 0, 0, 0, 0]
```

---

## Read A Syndrome

`read_syndrome(state)` measures every stabilizer generator using a temporary
ancilla that is added and removed internally.

```python
from stabilizer_python import BitFlip3Code

state = BitFlip3Code.zero_state()
state.x(1)

print(BitFlip3Code.read_syndrome(state))
# [1, 1]
```

Syndrome bit convention:

| Bit | Meaning |
|---:|---|
| `0` | check has eigenvalue `+1` |
| `1` | check has eigenvalue `-1` |

For the bit-flip code:

| Syndrome | X error |
|---|---|
| `[0, 0]` | none |
| `[1, 0]` | qubit 0 |
| `[1, 1]` | qubit 1 |
| `[0, 1]` | qubit 2 |

---

## Reuse A Syndrome Extractor

For repeated rounds, use `syndrome_extractor(state)`.

```python
from stabilizer_python import BitFlip3Code

state = BitFlip3Code.zero_state()
extractor = BitFlip3Code.syndrome_extractor(state)

print(extractor.extract())  # [0, 0]
state.x(0)
print(extractor.extract())  # [1, 0]
```

This keeps an ancilla attached to the state. That is useful for repeated QEC
rounds, but it means `state.n` increases while the extractor is alive.

Use `read_syndrome(state)` when you want the state size restored after a single
extraction.

---

## Logical Operators

Named codes provide explicit logical operators:

```python
from stabilizer_python import PerfectCode

print(PerfectCode.logical_x())
# +XXXXX

print(PerfectCode.logical_z())
# +ZZZZZ
```

For custom codes, logical operators can be supplied or computed lazily:

```python
code = StabilizerCode(
    n=3,
    k=1,
    generators=["+XXI", "+IXX"],
    name="PhaseFlip",
)

print(code.logical_x())
print(code.logical_z())
```

A logical operator must:

1. commute with every stabilizer generator
2. not be a product of stabilizer generators
3. anticommute with its paired logical operator

---

## Distance

`distance()` searches for the minimum-weight non-trivial logical operator.

```python
from stabilizer_python import PerfectCode, SteaneCode

print(PerfectCode.distance())  # 3
print(SteaneCode.distance())   # 3
```

The search is exact for the small named codes. It is exponential in `n`, so it is
not intended for large production-scale codes.

---

## Build A Custom Code

Example: phase-flip repetition code.

```python
from stabilizer_python import StabilizerCode

PhaseFlip = StabilizerCode(
    n=3,
    k=1,
    generators=["+XXI", "+IXX"],
    name="PhaseFlip",
    logical_xs=["+IIX"],
    logical_zs=["+ZZZ"],
)

state = PhaseFlip.zero_state()
state.z(1)
print(PhaseFlip.read_syndrome(state))
# [1, 1]
```

If you omit `logical_xs` and `logical_zs`, the code attempts to compute them
from the symplectic complement.

---

## Validation Errors

The constructor rejects malformed code definitions early.

```python
from stabilizer_python import StabilizerCode

StabilizerCode(n=3, k=1, generators=["+ZZI"])
# ValueError: expected 2 generators

StabilizerCode(n=2, k=0, generators=["+XX", "+ZI"])
# ValueError: generators anticommute

StabilizerCode(n=3, k=1, generators=["+ZZI", "+ZZI"])
# ValueError: generators do not have rank n-k
```

For the full validation and input-processing flow, see
[Architecture: Input Processing](../architecture/input-processing.md).

---

## Next: Noisy Benchmarks

Once a code can prepare states and read syndromes, it can be used directly with
the E4 benchmarking helpers:

```python
from stabilizer_python import BitFlip3Code, benchmark_code, build_lookup_decoder
from stabilizer_python.noise import apply_bit_flip_all

decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
result = benchmark_code(
    BitFlip3Code,
    noise_model=lambda st: apply_bit_flip_all(st, p=0.05, qubits=[0, 1, 2]),
    decoder=decoder,
    n_shots=500,
    seed=42,
)
print(result.summary())
```

For threshold scans and circuit-level noise, see
[Noise And Benchmarking](benchmarking.md).
