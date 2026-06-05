# Building Circuits

`Circuit` is a fluent builder for operation lists. It records gates, then applies them when you call `run(state)`.

```python
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(2)
circuit = Circuit(2).h(0).cnot(0, 1)
circuit.run(st)

print(st.inspect(views=["stabilizers"]))
```

Output:

```text
+XX
+ZZ
```

Those are the stabilizers of the Bell state $|\Phi^+\rangle$.

## Circuit Size

The circuit constructor takes the number of qubits the circuit expects:

```python
circuit = Circuit(5)
```

The state passed to `run()` must have at least that many qubits:

```python
st = StabilizerState.zero(5)
circuit.run(st)
```

## Chaining Gates

Every builder method returns `self`, so circuits can be written as chains:

```python
circuit = (
    Circuit(3)
    .h(0)
    .cnot(0, 1)
    .cnot(0, 2)
)
```

This prepares a 3-qubit GHZ state. Its stabilizers are:

```python
st = StabilizerState.zero(3)
circuit.run(st)
print(st.inspect(views=["stabilizers"]))
```

```text
+XXX
+ZZI
+ZIZ
```

## Clifford Circuit Methods

| Method | Gate |
|---|---|
| `.h(q)` | Hadamard |
| `.s(q)` | Phase (`S`) |
| `.sdg(q)` | `S` dagger |
| `.sx(q)` | Square-root X |
| `.sxdg(q)` | Square-root X dagger |
| `.x(q)` | Pauli `X` |
| `.y(q)` | Pauli `Y` |
| `.z(q)` | Pauli `Z` |
| `.i(q)` | Identity |
| `.cnot(c, t)` / `.cx(c, t)` | Controlled-NOT |
| `.cz(c, t)` | Controlled-Z |
| `.cy(c, t)` | Controlled-Y |
| `.ch(c, t)` | Controlled-H |
| `.swap(q1, q2)` | SWAP |
| `.iswap(q1, q2)` | iSWAP |
| `.cs(c, t)` | Controlled-S |
| `.csdg(c, t)` | Controlled-S dagger |
| `.ecr(q1, q2)` | Echoed cross-resonance |
| `.dcx(q1, q2)` | Double-CNOT |
| `.mz(q, key=None)` | Z-basis measurement |

## Measurement Outcomes

`run(state)` returns one outcome for every `.mz()` operation, in order:

```python
st = StabilizerState.zero(2)
outcomes = Circuit(2).h(0).cnot(0, 1).mz(0).mz(1).run(st)
print(outcomes)  # e.g. [0, 0] or [1, 1]
```

The outcomes are random, but they are correlated because this is a Bell state.

## Lower-Level Gate Objects

For the full gate library, use `.gate(gate_obj, qubits)` or the non-Clifford methods described in [Hybrid Simulation](non-clifford.md).

```python
from stabilizer_python import Circuit, HGate

circuit = Circuit(1).gate(HGate, [0])
```
