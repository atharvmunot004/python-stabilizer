# Qiskit Circuit Conversion

This page explains what `from_qiskit()` does under the hood when it converts a
Qiskit `QuantumCircuit` into a local `Circuit`.

For usage examples, see [Qiskit Interop](getting-started/qiskit.md). For
method signatures, see [`qiskit_interop`](api-reference.md#qiskit_interop).

---

## Entry point

```python
from stabilizer_python.qiskit_interop import from_qiskit

local = from_qiskit(qc)
local.run(sim)  # StabilizerState or QuantumSimulator
```

`from_qiskit(qc)` creates an empty local `Circuit(qc.num_qubits)` and walks
`qc.data` instruction by instruction. The returned `Circuit` is a plain
operation list — no simulation happens until you call `.run(state)`.

Source: [`stabilizer_python/qiskit_interop.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/qiskit_interop.py)

---

## Reading `QuantumCircuit.data`

Qiskit stores circuit instructions in `qc.data`. Each entry is a
`CircuitInstruction` with three fields the converter uses:

| Field | Type | Meaning |
|---|---|---|
| `instruction.operation.name` | `str` | Gate name, e.g. `"h"`, `"cx"`, `"rz"` |
| `instruction.operation.params` | list | Numeric gate parameters |
| `instruction.qubits` | tuple | Target `Qubit` objects for this instruction |

Conceptually:

```python
for instruction in qc.data:
    name = instruction.operation.name
    params = instruction.operation.params
    qubits = instruction.qubits
    # map qubits -> local indices, then append to local Circuit
```

---

## Qubit index resolution

Qiskit qubits are register objects, not plain integers. The converter resolves
each qubit to a flat index in the circuit's qubit list:

```python
qubits = [qc.find_bit(qubit).index for qubit in instruction.qubits]
```

That integer is what gets passed to local gate methods such as `.h(0)` or
`.cnot(0, 1)`.

For the top-level circuit, indices are `0..n-1` in register order. When a
composite instruction is expanded from its definition, indices are remapped
through the outer instruction's qubit list so nested gates target the correct
physical qubits.

---

## Gate name mapping

Most Qiskit gate names map directly to local `Circuit` methods. A few names
are renamed:

| Qiskit name | Local name | Notes |
|---|---|---|
| `cx` | `cnot` | Controlled-X |
| `measure` | `mz` | Z-basis measurement |
| `u1` | `p` | Phase gate |
| `u3` | `u` | General single-qubit unitary |
| `id` | `i` | Identity |
| all others | same name | e.g. `h`, `t`, `ccx`, `crz` |

In code this is not a separate dictionary constant — `_append_instruction()`
branches on `operation.name` and calls the matching `Circuit` builder method.

Supported fixed gates include `h`, `s`, `sdg`, `sx`, `sxdg`, `x`, `y`, `z`,
`t`, `tdg`, `cy`, `cz`, `ch`, `swap`, `iswap`, `ecr`, `dcx`, `cs`, `csdg`,
`ccx`, `toffoli`, `ccz`, `cswap`, and `fredkin`.

Supported parameterized gates include `rx`, `ry`, `rz`, `p`, `u2`, `u`, `r`,
`crx`, `cry`, `crz`, `cp`, `rxx`, `ryy`, `rzz`, `rzx`, `xx_plus_yy`, and
`xx_minus_yy`.

---

## Parameters must be numeric

Before appending a gate, the converter tries to cast each parameter to `float`:

```python
params.append(float(param))
```

If a parameter is still an unbound Qiskit `ParameterExpression`, conversion
raises:

```text
ValueError: unbound parameter in Qiskit instruction: <gate_name>
```

Bind parameters first:

```python
bound = qc.assign_parameters({theta: math.pi / 4})
from_qiskit(bound)
```

---

## Skipped instructions

These Qiskit instructions are silently ignored:

- `barrier`
- `delay`

They carry no unitary action, so dropping them does not change simulation
results.

---

## Composite gate expansion

If an instruction name is not handled directly and Qiskit provides a
decomposition, the converter recurses into `operation.definition`:

```python
if operation.definition is not None:
    _append_circuit(out, operation.definition, qubits)
```

This is how library gates such as decomposed `QFT` blocks become sequences of
local `h`, `cnot`, and rotation gates. The nested circuit's qubits are remapped
through the outer instruction's resolved qubit list.

If a gate is unknown and has no definition, conversion raises:

```text
ValueError: unsupported Qiskit instruction: <gate_name>
```

The error includes the gate name so missing support is easy to spot and add.

---

## End-to-end walkthrough

Consider:

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure(0, 0)
```

Conversion proceeds as:

| Step | Qiskit instruction | Local operation appended |
|---|---|---|
| 1 | `h` on qubit 0 | `.h(0)` |
| 2 | `cx` on qubits 0, 1 | `.cnot(0, 1)` |
| 3 | `measure` on qubit 0 | `.mz(0)` |

The classical bit index in `qc.measure(0, 0)` is ignored — local simulation
records only the quantum measurement outcome via `.mz()`.

Running on a simulator:

```python
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

sim = QuantumSimulator(2)
outcomes = from_qiskit(qc).run(sim)
```

Because this circuit is pure Clifford until measurement, `sim.mode` stays
`"tableau"` through the gates. Measurements delegate to the active backend.

---

## What is not converted

- Classical registers and classical logic
- Mid-circuit measurements with conditional operations (only direct `measure` → `mz` is supported)
- Unbound symbolic parameters
- Unknown gates without a Qiskit definition

---

## Related pages

- [Qiskit Interop examples](getting-started/qiskit.md)
- [Comparison with Qiskit's Clifford](theory/tableau.md#comparison-with-qiskits-clifford)
- [`qiskit_interop` API reference](api-reference.md#qiskit_interop)
- [Architecture: qiskit_interop module](architecture.md#qiskit_interop)
