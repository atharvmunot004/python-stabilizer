# Tracing Syndrome Extraction

`TracedCircuit` records the tableau after every gate and every measurement in a Clifford circuit. It is the main pedagogical tool for seeing how syndrome ancillas become entangled with data qubits and then collapse on measurement.

## Quick Example

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tracing import TracedCircuit

st = StabilizerState.zero(5)   # q0-q2 data, q3-q4 ancilla
BitFlip3Code.encoder_circuit().run(st)
st.x(1)                        # inject an X error on q1

tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
outcomes = tc.run(st)

print(outcomes)   # [1, 1]
tc.print_trace()
```

Run the packaged demo:

```bash
python -m stabilizer_python.examples.bitflip3_trace_demo
```

## What Gets Recorded

Each recorded step is a `TraceStep` with:

| Field | Meaning |
|---|---|
| `index` | 1-based step number in the circuit |
| `op_label` | Human-readable operation, e.g. `CNOT(0, 3)` or `MZ(3, key='s01')` |
| `kind` | `"gate"` or `"measurement"` |
| `state` | Snapshot of the tableau after the operation |
| `outcome` | Measurement bit for `MZ` steps (`0` or `1`) |
| `measurement_branch` | `"deterministic"` or `"random"` for `MZ` steps |

Access steps programmatically:

```python
for step in tc.steps:
    print(step.op_label, step.kind)
    print(step.state.inspect())
```

## Bit-Flip Syndrome Circuit Step By Step

`BitFlip3Code.syndrome_circuit()` performs six operations on five qubits:

| Step | Operation | What happens |
|---|---|---|
| 1 | `CNOT(0, 3)` | Copy $Z_0$ parity onto ancilla q3 |
| 2 | `CNOT(1, 3)` | Combine with $Z_1$ so q3 tracks $Z_0Z_1$ |
| 3 | `MZ(3, key='s01')` | Measure ancilla q3, read syndrome bit `s01` |
| 4 | `CNOT(1, 4)` | Copy $Z_1$ parity onto ancilla q4 |
| 5 | `CNOT(2, 4)` | Combine with $Z_2$ so q4 tracks $Z_1Z_2$ |
| 6 | `MZ(4, key='s12')` | Measure ancilla q4, read syndrome bit `s12` |

After steps 1-2, ancilla q3 is entangled with the data qubits through the stabilizer group update. Step 3 collapses that entanglement into a single syndrome bit and rewrites the tableau.

## Example Trace Output

For an encoded $|0_L\rangle$ with no error, a trace looks like:

```text
Step 1: CNOT(0, 3)
+XXIII
+IXIII
+IIXII
+IIIXI
+IIIIX
---
+ZZIII
+IZZII
+IIZZI
+IIIZZ
+IIIII

Step 3: MZ(3, key='s01')
  outcome=0 (deterministic)
...
```

For an `X` error on q1, the same circuit returns `outcomes == [1, 1]`.

## Deterministic vs Random Measurements

Before each `MZ`, `TracedCircuit` calls `z_measurement_branch(q)` on the tableau. That reports whether `measure_z(q)` will take the deterministic path or sample randomly.

For a valid encoded state with no error, the parity measurements are usually deterministic. After an uncorrected error, the syndrome bits are still deterministic readings of the corrupted stabilizer group — the random branch appears when measuring an observable that anticommutes with the current stabilizer generators.

## Syndrome Circuit vs `measure_syndrome()`

Two APIs measure the same parities:

| API | What it does |
|---|---|
| `BitFlip3Code.syndrome_circuit()` | CNOT + measure ancillas; leaves ancillas in post-measurement states |
| `BitFlip3Code.measure_syndrome(st)` | Imperative CNOT + measure + `reset_z()` on each ancilla |

Use `TracedCircuit` with `syndrome_circuit()` when you want a step-by-step circuit trace. Use `measure_syndrome()` when you want the full measure-and-reset workflow in one call.

## Disabling The Trace

```python
tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=False)
outcomes = tc.run(st)
assert tc.steps == []
```

Use `trace=False` for bulk simulation. Tracing copies the full tableau after
every step; that is useful for teaching but expensive in tight loops such as
1000-shot syndrome benchmarking.

## Limits

- `TracedCircuit` requires Clifford operations in tableau mode.
- Non-Clifford gates in the wrapped circuit raise `ValueError` during tracing.
- Tracing works on `StabilizerState` directly; it mutates the passed state in place.

For the underlying measurement algorithm, see [Measurement](../theory/measurement.md). For code theory, see [Error-Correcting Codes](../theory/qec-codes.md).
