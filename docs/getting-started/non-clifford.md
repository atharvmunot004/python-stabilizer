# Hybrid Simulation

`StabilizerState` is fast because it only supports Clifford operations. Non-Clifford gates do not preserve a single stabilizer tableau description.

Use `QuantumSimulator` when your circuit may contain:

- `T` or `Tdg`
- rotations such as `RX`, `RY`, `RZ`
- Toffoli / `CCX`
- arbitrary `Gate` objects
- Qiskit circuits with a mix of gates

## First Non-Clifford Gate

`QuantumSimulator` starts in tableau mode. It switches to statevector mode at the first non-Clifford gate.

```python
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(1)
sim.apply("h", [0])
print(sim.mode)  # "tableau"

sim.apply("t", [0])
print(sim.mode)  # "statevector"
print(sim.sv.data)
```

The switch is one-way. Once the simulator is in statevector mode, later Clifford gates are also applied to the statevector backend.

## Single-Qubit Rotations

```python
import math
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(1)
sim.apply("rx", [0], params=[math.pi / 4])
sim.apply("ry", [0], params=[math.pi / 5])
sim.apply("rz", [0], params=[math.pi / 6])
print(sim.statevector_snapshot().to_dict())
```

## Two-Qubit Parameterized Gates

```python
import math
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(2)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("crz", [0, 1], params=[math.pi / 3])
sim.apply("rzz", [0, 1], params=[math.pi / 4])
print(sim.sv.probabilities())
```

## Toffoli

```python
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(3)
sim.apply("x", [1])
sim.apply("x", [2])
sim.apply("ccx", [1, 2, 0])

print(sim.statevector_snapshot().to_dict())  # {'111': (1+0j)}
```

## Circuit With Non-Clifford Gates

```python
import math
from stabilizer_python import Circuit, QuantumSimulator

circuit = Circuit(3).h(0).t(0).rx(math.pi / 4, 1).ccx(0, 1, 2)

sim = QuantumSimulator(3)
circuit.run(sim)
print(sim.mode)  # "statevector"
```

## Statevector Inspection

You can inspect the current statevector from either mode:

```python
sv = sim.statevector_snapshot()
print(sv.data)
print(sv.probabilities())
print(sv.to_dict())
```

## Gate-by-Gate Tracing

Pass `trace=True` to record the state after every gate:

```python
import math
from stabilizer_python import QuantumSimulator

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

Each trace step records the gate name, qubit targets, parameters, mode before
and after the gate, and a snapshot of the active backend. This is useful for
seeing exactly when the simulator switches from tableau to statevector mode.

For the backend design, see [Hybrid Simulation](../hybrid-simulation.md).
