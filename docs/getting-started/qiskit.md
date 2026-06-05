# Qiskit Interop

Qiskit is optional. Install it when you want to load Qiskit circuits:

```bash
pip install qiskit
```

Then convert a Qiskit `QuantumCircuit` with `from_qiskit()`.

## Pure Clifford Qiskit Circuit

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2)
qc.h(0)
qc.cx(0, 1)

sim = QuantumSimulator(2)
from_qiskit(qc).run(sim)

print(sim.mode)  # "tableau"
print(sim.tableau.inspect(views=["stabilizers"]))
```

Because the circuit is pure Clifford, it stays in tableau mode.

## Non-Clifford Qiskit Circuit

```python
import math
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2)
qc.h(0)
qc.t(0)
qc.cx(0, 1)
qc.rz(math.pi / 4, 1)

sim = QuantumSimulator(2)
from_qiskit(qc).run(sim)

print(sim.mode)  # "statevector"
print(sim.sv.data)
```

The first non-Clifford gate triggers statevector mode.

## Qiskit Circuit Library

```python
from qiskit.circuit.library import QFT
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QFT(3, do_swaps=True).decompose()

sim = QuantumSimulator(3)
from_qiskit(qc).run(sim)

print(sim.sv.probabilities())
```

## Parameterized Circuits

Bind parameters before conversion:

```python
import math
from qiskit.circuit.library import RealAmplitudes
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

ansatz = RealAmplitudes(2, reps=1)
bound = ansatz.assign_parameters([math.pi / 4, math.pi / 3, math.pi / 2, math.pi / 6])

sim = QuantumSimulator(2)
from_qiskit(bound).run(sim)
print(sim.sv.to_dict())
```

Unbound parameter expressions raise `ValueError`.

## Measurements

```python
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure(0, 0)
qc.measure(1, 1)

sim = QuantumSimulator(2)
outcomes = from_qiskit(qc).run(sim)
print(outcomes)  # e.g. [0, 0] or [1, 1]
```

## Gate Name Mappings

| Qiskit name | Local name |
|---|---|
| `cx` | `cnot` |
| `measure` | `mz` |
| `u1` | `p` |
| `u3` / `u` | `u` |
| `tdg` | `tdg` |
| `ccx` | `ccx` |
| `cswap` | `cswap` |
| all others | same name |

`barrier` and `delay` are skipped. Unknown gates raise `ValueError` with the gate name.

For method-level details, see [`qiskit_interop`](../api-reference.md#qiskit_interop).
