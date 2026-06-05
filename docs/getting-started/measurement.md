# Measuring Qubits

The package supports Z-basis measurement. Outcomes are returned as bits:

- `0` means eigenvalue `+1`
- `1` means eigenvalue `-1`

## Measure Directly

```python
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

outcome = st.measure_z(0)
print(f"Outcome: {outcome}")
print(st.inspect(views=["chp"]))
```

For a Bell state, measuring one qubit is random, but it fixes the other qubit to the same value.

## Measure Inside A Circuit

Use `.mz(q)` to add a measurement operation to a `Circuit`:

```python
st = StabilizerState.zero(2)
circuit = Circuit(2).h(0).cnot(0, 1).mz(0).mz(1)

outcomes = circuit.run(st)
print(outcomes)  # e.g. [0, 0] or [1, 1]
```

The returned list contains one item per `.mz()` operation, in order.

## Measurement Keys

You can attach a readable key to a measurement:

```python
circuit = Circuit(2).h(0).cnot(0, 1).mz(0, key="left").mz(1, key="right")
outcomes = circuit.run(st)
```

The current `run()` API still returns an ordered list. The key is stored in the operation label and is used by tracing output.

## Deterministic vs Random Branches

`StabilizerState.measure_z(q)` chooses one of two paths:

| Branch | When it happens |
|---|---|
| deterministic | The stabilizer group already fixes the Z value of qubit `q` |
| random | Some stabilizer generator anticommutes with `Z_q` |

You can ask which branch an upcoming Z measurement will take:

```python
branch = st.z_measurement_branch(0)
print(branch)  # "deterministic" or "random"
```

This is useful for teaching and for traced QEC examples.

## Reset To `|0>`

`reset_z(q)` measures in the Z basis and applies `X` if the result was `1`:

```python
outcome = st.reset_z(0)
```

Afterward, qubit `0` is in the `|0>` state.

For the full measurement algorithm, see [Measurement](../theory/measurement.md).
