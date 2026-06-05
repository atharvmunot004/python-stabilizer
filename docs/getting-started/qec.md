# QEC Examples

The package includes educational quantum error-correction examples. They are designed to expose the tableau mechanics rather than hide them behind a black-box API.

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

## Syndrome Circuit

The explicit syndrome circuit uses two ancillas:

```python
circuit = BitFlip3Code.syndrome_circuit()
```

It measures:

- `s01`: $Z_0Z_1$ using ancilla q3
- `s12`: $Z_1Z_2$ using ancilla q4

## Tracing Syndrome Extraction

Use `TracedCircuit` to see every CNOT and measurement step:

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

Each trace step includes:

- the operation label, such as `CNOT(0, 3)`
- measurement outcome for `MZ` operations
- whether the measurement branch was `deterministic` or `random`
- the tableau after the operation

This is the most useful beginner tool for seeing how syndrome ancillas become entangled with data qubits and then collapse on measurement.

## Shor 9-Qubit Code

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
