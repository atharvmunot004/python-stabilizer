# QEC Examples

The package includes two QEC layers:

- `StabilizerCode`, the general `[[n,k,d]]` code abstraction for named and custom
  stabilizer codes
- `stabilizer_python.codes`, the older explicit-circuit examples retained for
  backwards-compatible pedagogy

For a focused tutorial on the new API, see
[General Stabilizer Codes](stabilizer-codes.md).

---

## General StabilizerCode API

Use top-level named instances for common codes:

```python
from stabilizer_python import SteaneCode, PerfectCode, BitFlip3Code

st = SteaneCode.zero_state()
print(SteaneCode.read_syndrome(st))
# [0, 0, 0, 0, 0, 0]

print(PerfectCode.distance())
# 3

st2 = BitFlip3Code.zero_state()
st2.x(1)
print(BitFlip3Code.read_syndrome(st2))
# [1, 1]
```

The named instances are:

| Code | Parameters | Import |
|---|---|---|
| bit-flip repetition | `[[3,1,1]]` | `BitFlip3Code` |
| phase-flip repetition | `[[3,1,1]]` | `PhaseFlip3Code` |
| 5-qubit perfect | `[[5,1,3]]` | `PerfectCode` |
| Steane | `[[7,1,3]]` | `SteaneCode` |
| Shor | `[[9,1,3]]` | `Shor9Code` |
| distance-3 surface-code-style | `[[9,1,3]]` | `SurfaceCode3` |

You can define a custom code directly:

```python
from stabilizer_python import StabilizerCode

PhaseFlip = StabilizerCode(
    n=3,
    k=1,
    generators=["+XXI", "+IXX"],
    logical_xs=["+IIX"],
    logical_zs=["+ZZZ"],
    name="PhaseFlip",
)
```

The constructor validates generator count, Pauli-string length, Pauli
characters, GF(2) rank, commutation, and provided logical operators.

---

## Syndrome Extraction

`StabilizerCode.read_syndrome(state)` measures every stabilizer generator using
a temporary ancilla and removes that ancilla before returning:

```python
from stabilizer_python import PerfectCode

state = PerfectCode.zero_state()
state.x(2)
syndrome = PerfectCode.read_syndrome(state)
print(syndrome)
```

For repeated rounds, use a reusable extractor:

```python
from stabilizer_python import BitFlip3Code

state = BitFlip3Code.zero_state()
extractor = BitFlip3Code.syndrome_extractor(state)

print(extractor.extract())  # [0, 0]
state.x(0)
print(extractor.extract())  # [1, 0]
```

The extractor keeps an ancilla attached to the state so it can reuse it.

---

## Logical Tracking, Noise, And Benchmarks

For logical readout and decoder benchmarks, use the newer E2-E4 helpers:

- `EncodedState` wraps a physical `StabilizerState` with a code's logical
  operators and checks residual logical errors.
- `stabilizer_python.noise` provides sampled Pauli channels such as
  `apply_bit_flip_all()` and `apply_depolarizing_all()`.
- `benchmark_code()` runs encode -> noise -> syndrome -> decode -> logical
  error checks for many shots.
- `threshold_scan()` sweeps physical error rates for threshold plots.

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

print(result.logical_error_rate)
```

For the full workflow, see [Noise And Benchmarking](benchmarking.md).

---

## Legacy Explicit-Circuit Examples

The older `stabilizer_python.codes` classes are still useful when you want to
see the exact encoder or syndrome circuit as a `Circuit`.

## 3-Qubit Bit-Flip Code

The 3-qubit repetition code protects against a single `X` error.

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code

st = StabilizerState.zero(5)  # q0-q2 data, q3-q4 ancilla
BitFlip3Code.encoder_circuit().run(st)

st.x(2)  # inject an X error on q2

s01, s12 = BitFlip3Code.measure_syndrome(st)
BitFlip3Code.correct_x_from_syndrome(st, s01, s12)

print(f"Syndrome: ({s01}, {s12})")
print(st.inspect(views=["stabilizers"]))
```

Syndrome interpretation:

| Syndrome | Meaning |
|:---:|---|
| `(0, 0)` | No detected X error |
| `(1, 0)` | X error on q0 |
| `(1, 1)` | X error on q1 |
| `(0, 1)` | X error on q2 |

## Legacy Syndrome Circuit

The explicit syndrome circuit uses two ancillas:

```python
circuit = BitFlip3Code.syndrome_circuit()
```

It measures:

- `s01`: $Z_0Z_1$ using ancilla q3
- `s12`: $Z_1Z_2$ using ancilla q4

## Tracing Syndrome Extraction

Use `TracedCircuit` to see every CNOT and measurement step. For a full walkthrough with example output, see [Tracing Syndrome Extraction](tracing.md).

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tracing import TracedCircuit

st = StabilizerState.zero(5)
BitFlip3Code.encoder_circuit().run(st)
st.x(1)

tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
outcomes = tc.run(st)

print(outcomes)
tc.print_trace()
```

Each trace step includes the operation label, measurement outcome and branch for `MZ` operations, and the CHP tableau after the step.

`BitFlip3Code.syndrome_circuit()` measures ancillas but does not reset them. For measure-and-reset in one call, use `BitFlip3Code.measure_syndrome(st)`.

## Legacy Shor 9-Qubit Code

The Shor example builds the 9-qubit encoder and includes an `X`-error syndrome helper:

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import Shor9Code

st = StabilizerState.zero(9)
Shor9Code.encoder_circuit().run(st)

st.x(7)
syndrome = Shor9Code.read_syndrome(st)
Shor9Code.correct_x_from_syndrome(st, syndrome)
```

For the code theory and stabilizer layouts, see [Error-Correcting Codes](../theory/qec-codes.md).
