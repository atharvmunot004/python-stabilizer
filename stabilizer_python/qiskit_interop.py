from __future__ import annotations

from typing import Any, List

from .circuit import Circuit


def from_qiskit(qc: Any) -> Circuit:
    """Convert a Qiskit QuantumCircuit into a local Circuit."""
    out = Circuit(qc.num_qubits)
    _append_circuit(out, qc, [i for i in range(qc.num_qubits)])
    return out


def _append_circuit(out: Circuit, qc: Any, qubit_map: List[int]) -> None:
    for instruction in qc.data:
        operation = instruction.operation
        name = operation.name
        qubits = [qubit_map[qc.find_bit(qubit).index] for qubit in instruction.qubits]
        if name in ("barrier", "delay"):
            continue
        if _append_instruction(out, name, qubits, _numeric_params(operation)):
            continue
        if operation.definition is not None:
            _append_circuit(out, operation.definition, qubits)
            continue
        raise ValueError("unsupported Qiskit instruction: {}".format(name))


def _numeric_params(operation: Any) -> List[float]:
    params = []
    for param in operation.params:
        try:
            params.append(float(param))
        except TypeError as exc:
            raise ValueError("unbound parameter in Qiskit instruction: {}".format(operation.name)) from exc
    return params


def _append_instruction(out: Circuit, name: str, qubits: List[int], params: List[float]) -> bool:
    if name == "measure":
        out.mz(qubits[0])
        return True
    if name in ("id", "i"):
        out.i(qubits[0])
        return True
    if name in ("h", "s", "sdg", "sx", "sxdg", "x", "y", "z", "t", "tdg"):
        getattr(out, name)(qubits[0])
        return True
    if name in ("rx", "ry", "rz", "p", "u1"):
        _require_params(name, params, 1)
        method = "p" if name == "u1" else name
        getattr(out, method)(params[0], qubits[0])
        return True
    if name == "u2":
        _require_params(name, params, 2)
        out.u2(params[0], params[1], qubits[0])
        return True
    if name in ("u", "u3"):
        _require_params(name, params, 3)
        out.u(params[0], params[1], params[2], qubits[0])
        return True
    if name == "r":
        _require_params(name, params, 2)
        out.r(params[0], params[1], qubits[0])
        return True
    if name in ("cx", "cnot"):
        out.cnot(qubits[0], qubits[1])
        return True
    if name in ("cy", "cz", "ch", "swap", "iswap", "ecr", "dcx", "cs", "csdg"):
        getattr(out, name)(qubits[0], qubits[1])
        return True
    if name in ("crx", "cry", "crz", "cp", "rxx", "ryy", "rzz", "rzx"):
        _require_params(name, params, 1)
        getattr(out, name)(params[0], qubits[0], qubits[1])
        return True
    if name in ("xx_plus_yy", "xx_minus_yy"):
        _require_params(name, params, 2)
        getattr(out, name)(params[0], params[1], qubits[0], qubits[1])
        return True
    if name in ("ccx", "toffoli", "ccz"):
        getattr(out, name)(qubits[0], qubits[1], qubits[2])
        return True
    if name in ("cswap", "fredkin"):
        getattr(out, name)(qubits[0], qubits[1], qubits[2])
        return True
    return False


def _require_params(name: str, params: List[float], count: int) -> None:
    if len(params) != count:
        raise ValueError("Qiskit instruction {} expects {} parameter(s)".format(name, count))
