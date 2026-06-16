# Noise And Benchmarking

This page connects the E1-E4 QEC workflow:

1. Define or import a `StabilizerCode`.
2. Prepare a logical zero codeword.
3. Apply sampled Pauli noise.
4. Extract a syndrome.
5. Decode the syndrome into corrections.
6. Use `EncodedState` or `benchmark_code()` to detect residual logical errors.

The APIs are intentionally small and pure Python. They are designed for
educational Monte Carlo experiments and paper-figure prototypes on small codes.

---

## Sample Pauli Noise

The functions in `stabilizer_python.noise` apply one sampled Pauli error per
call and mutate the `StabilizerState` in place.

```python
from stabilizer_python import BitFlip3Code
from stabilizer_python.noise import apply_bit_flip_all, apply_depolarizing_all

state = BitFlip3Code.zero_state()

errors = apply_bit_flip_all(state, p=0.05, qubits=[0, 1, 2])
print(errors)  # one of "I" or "X" per target qubit

errors = apply_depolarizing_all(state, p=0.01)
print(errors)  # one of "I", "X", "Y", or "Z" per qubit
```

Available single-qubit channels:

| Function | Error model |
|---|---|
| `apply_pauli_channel(state, q, p_x, p_y, p_z)` | custom Pauli channel |
| `apply_depolarizing(state, q, p)` | `X/Y/Z` each with probability `p/3` |
| `apply_bit_flip(state, q, p)` | `X` with probability `p` |
| `apply_phase_flip(state, q, p)` | `Z` with probability `p` |
| `apply_bit_phase_flip(state, q, p)` | `Y` with probability `p` |

The `_all` variants apply independent samples to every qubit or to the supplied
`qubits` list.

---

## Logical State Tracking

`EncodedState` wraps a `StabilizerState` and a code object. It knows the code's
logical operators, can read logical observables, and can identify residual
logical errors after correction.

```python
from stabilizer_python import BitFlip3Code, EncodedState

state = BitFlip3Code.zero_state()
enc = EncodedState(state, BitFlip3Code)

print(enc.logical_z_eigenvalue())  # +1 for |0_L>
print(enc.logical_state_string())  # |0_L>
print(enc.is_valid_codeword())     # True

state.x(0)
print(enc.syndrome())              # [1, 0]
print(enc.has_logical_error())     # False: single X error is detectable
```

For intentional logical operations, apply them through the wrapper so the
logical frame is updated:

```python
enc.apply_logical_x()
print(enc.logical_state_string())  # |1_L>
print(enc.has_logical_error())     # False: this was intentional
```

---

## Build A Lookup Decoder

`build_lookup_decoder(code, max_errors=1)` enumerates Pauli errors up to a given
weight, records their syndromes, and returns a decoder function:

```python
from stabilizer_python import BitFlip3Code, build_lookup_decoder

decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)

print(decoder([0, 0]))  # []
print(decoder([1, 0]))  # [(0, "X")]
print(decoder([1, 1]))  # [(1, "X")]
print(decoder([0, 1]))  # [(2, "X")]
```

This is a minimum-weight lookup table for small codes. The number of enumerated
errors grows quickly with `n`, `max_errors`, and the three non-identity Pauli
choices.

---

## Benchmark One Code

`benchmark_code()` is the high-level E4 wrapper. Each shot creates a fresh
`StabilizerState.zero(code.n)`, calls `code.encode(state)`, applies your noise
model, extracts `code.read_syndrome(state)`, applies decoder corrections, and
checks logical errors with `EncodedState`.

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
print(result.summary())
```

`CodeBenchmarkResult` stores:

| Field | Meaning |
|---|---|
| `n_shots` | total Monte Carlo shots |
| `n_logical_errors` | shots with any residual logical error |
| `logical_error_rate` | `n_logical_errors / n_shots` |
| `n_x_errors`, `n_z_errors` | residual logical X/Z counts |
| `x_error_rate`, `z_error_rate` | per-shot logical X/Z rates |
| `elapsed_seconds` | wall-clock time |
| `shots_per_second` | measured throughput |
| `seed` | random seed used |
| `records` | optional per-shot `ShotRecord` list |

Pass `record_shots=True` when debugging a decoder. Each `ShotRecord` stores the
shot index, syndrome, correction, logical error type, and whether a logical
error occurred.

---

## Threshold Scans

`threshold_scan()` sweeps physical error rates and returns a
`ThresholdScanResult`.

```python
from stabilizer_python import BitFlip3Code, build_lookup_decoder, threshold_scan
from stabilizer_python.noise import apply_bit_flip_all

decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)

scan = threshold_scan(
    BitFlip3Code,
    noise_model_factory=lambda p: (
        lambda st: apply_bit_flip_all(st, p=p, qubits=[0, 1, 2])
    ),
    decoder=decoder,
    p_values=[0.01, 0.05, 0.10, 0.20],
    n_shots_per_p=200,
    seed=0,
    verbose=False,
)

print(scan.as_dict())
print(scan.summary())
```

`scan.as_dict()` returns `{physical_error_rate: logical_error_rate}` for quick
plotting. The full `benchmark_results` list keeps every `CodeBenchmarkResult`
for reproducibility.

Use `compare_codes()` when you want to run the same threshold scan across
multiple code objects with per-code decoders.

---

## NoisyCircuit

`NoisyCircuit` is a `Circuit` subclass that injects simple Pauli noise during
execution:

- after each Clifford gate, it applies depolarizing noise with probability
  `gate_error` to the touched qubits
- before returning each measurement result, it flips the classical bit with
  probability `meas_error`

```python
from stabilizer_python import NoisyCircuit, StabilizerState

state = StabilizerState.zero(2)
circuit = NoisyCircuit(2, gate_error=0.01, meas_error=0.02)
circuit.h(0).cnot(0, 1).mz(0)

outcomes = circuit.run(state)
print(outcomes)
```

For decoder benchmarking against `StabilizerCode`, prefer `benchmark_code()`.
Use `NoisyCircuit` when you want circuit-level noise inserted while stepping
through a concrete Clifford circuit.
