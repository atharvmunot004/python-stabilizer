from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import List

import numpy as np


@dataclass(frozen=True)
class Gate:
    """Unitary gate metadata and matrix representation."""

    name: str
    num_qubits: int
    matrix: np.ndarray
    is_clifford: bool
    params: List[float]


I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
H = (1.0 / sqrt(2.0)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
P0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
P1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)


def _gate(name: str, num_qubits: int, matrix: np.ndarray, is_clifford: bool, params: List[float] | None = None) -> Gate:
    return Gate(name, num_qubits, np.asarray(matrix, dtype=np.complex128), is_clifford, [] if params is None else params)


def _controlled(target: np.ndarray) -> np.ndarray:
    return np.kron(I2, P0) + np.kron(target, P1)


def _rotation(pauli: np.ndarray, theta: float, name: str) -> Gate:
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    return _gate(name, 1, c * I2 - 1j * s * pauli, False, [theta])


def _pauli_rotation(pauli_a: np.ndarray, pauli_b: np.ndarray, theta: float, name: str) -> Gate:
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    return _gate(name, 2, c * np.eye(4, dtype=np.complex128) - 1j * s * np.kron(pauli_b, pauli_a), False, [theta])


IGate = _gate("i", 1, I2, True)
HGate = _gate("h", 1, H, True)
XGate = _gate("x", 1, X, True)
YGate = _gate("y", 1, Y, True)
ZGate = _gate("z", 1, Z, True)
SGate = _gate("s", 1, np.diag([1, 1j]), True)
SdgGate = _gate("sdg", 1, np.diag([1, -1j]), True)
SXGate = _gate("sx", 1, 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]), True)
SXdgGate = _gate("sxdg", 1, 0.5 * np.array([[1 - 1j, 1 + 1j], [1 + 1j, 1 - 1j]]), True)
TGate = _gate("t", 1, np.diag([1, np.exp(1j * pi / 4.0)]), False)
TdgGate = _gate("tdg", 1, np.diag([1, np.exp(-1j * pi / 4.0)]), False)


def RXGate(theta: float) -> Gate:
    """Return an Rx(theta) gate."""
    return _rotation(X, theta, "rx")


def RYGate(theta: float) -> Gate:
    """Return an Ry(theta) gate."""
    return _rotation(Y, theta, "ry")


def RZGate(theta: float) -> Gate:
    """Return an Rz(theta) gate."""
    return _gate("rz", 1, np.diag([np.exp(-0.5j * theta), np.exp(0.5j * theta)]), False, [theta])


def PhaseGate(lam: float) -> Gate:
    """Return a phase gate P(lambda)."""
    return _gate("p", 1, np.diag([1, np.exp(1j * lam)]), False, [lam])


def U1Gate(lam: float) -> Gate:
    """Return a U1(lambda) gate."""
    return _gate("u1", 1, PhaseGate(lam).matrix, False, [lam])


def U2Gate(phi: float, lam: float) -> Gate:
    """Return a U2(phi, lambda) gate."""
    m = (1.0 / sqrt(2.0)) * np.array(
        [[1, -np.exp(1j * lam)], [np.exp(1j * phi), np.exp(1j * (phi + lam))]],
        dtype=np.complex128,
    )
    return _gate("u2", 1, m, False, [phi, lam])


def U3Gate(theta: float, phi: float, lam: float) -> Gate:
    """Return a U3(theta, phi, lambda) gate."""
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    m = np.array(
        [[c, -np.exp(1j * lam) * s], [np.exp(1j * phi) * s, np.exp(1j * (phi + lam)) * c]],
        dtype=np.complex128,
    )
    return _gate("u3", 1, m, False, [theta, phi, lam])


def UGate(theta: float, phi: float, lam: float) -> Gate:
    """Return a U(theta, phi, lambda) gate."""
    return _gate("u", 1, U3Gate(theta, phi, lam).matrix, False, [theta, phi, lam])


def RGate(theta: float, phi: float) -> Gate:
    """Return an R(theta, phi) gate."""
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    m = np.array(
        [[c, -1j * np.exp(-1j * phi) * s], [-1j * np.exp(1j * phi) * s, c]],
        dtype=np.complex128,
    )
    return _gate("r", 1, m, False, [theta, phi])


CXGate = _gate("cx", 2, _controlled(X), True)
CNOTGate = _gate("cnot", 2, CXGate.matrix, True)
CYGate = _gate("cy", 2, _controlled(Y), True)
CZGate = _gate("cz", 2, _controlled(Z), True)
CHGate = _gate("ch", 2, _controlled(H), True)
SwapGate = _gate("swap", 2, np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]), True)
iSwapGate = _gate("iswap", 2, np.array([[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]]), True)
ECRGate = _gate(
    "ecr",
    2,
    (1.0 / sqrt(2.0)) * np.array([[0, 0, 1, 1j], [0, 0, 1j, 1], [1, -1j, 0, 0], [-1j, 1, 0, 0]]),
    True,
)
DCXGate = _gate("dcx", 2, CXGate.matrix @ np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128), False)
CSGate = _gate("cs", 2, _controlled(SGate.matrix), True)
CSdgGate = _gate("csdg", 2, _controlled(SdgGate.matrix), True)


def CRXGate(theta: float) -> Gate:
    """Return a controlled-Rx(theta) gate."""
    return _gate("crx", 2, _controlled(RXGate(theta).matrix), False, [theta])


def CRYGate(theta: float) -> Gate:
    """Return a controlled-Ry(theta) gate."""
    return _gate("cry", 2, _controlled(RYGate(theta).matrix), False, [theta])


def CRZGate(theta: float) -> Gate:
    """Return a controlled-Rz(theta) gate."""
    return _gate("crz", 2, _controlled(RZGate(theta).matrix), False, [theta])


def CPhaseGate(lam: float) -> Gate:
    """Return a controlled phase gate."""
    return _gate("cp", 2, _controlled(PhaseGate(lam).matrix), False, [lam])


def RXXGate(theta: float) -> Gate:
    """Return an RXX(theta) gate."""
    return _pauli_rotation(X, X, theta, "rxx")


def RYYGate(theta: float) -> Gate:
    """Return an RYY(theta) gate."""
    return _pauli_rotation(Y, Y, theta, "ryy")


def RZZGate(theta: float) -> Gate:
    """Return an RZZ(theta) gate."""
    return _pauli_rotation(Z, Z, theta, "rzz")


def RZXGate(theta: float) -> Gate:
    """Return an RZX(theta) gate."""
    return _pauli_rotation(Z, X, theta, "rzx")


def XXPlusYYGate(theta: float, beta: float) -> Gate:
    """Return an XXPlusYY(theta, beta) gate."""
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    m = np.array(
        [[1, 0, 0, 0], [0, c, -1j * np.exp(-1j * beta) * s, 0], [0, -1j * np.exp(1j * beta) * s, c, 0], [0, 0, 0, 1]],
        dtype=np.complex128,
    )
    return _gate("xx_plus_yy", 2, m, False, [theta, beta])


def XXMinusYYGate(theta: float, beta: float) -> Gate:
    """Return an XXMinusYY(theta, beta) gate."""
    c = cos(theta / 2.0)
    s = sin(theta / 2.0)
    m = np.array(
        [[c, 0, 0, -1j * np.exp(-1j * beta) * s], [0, 1, 0, 0], [0, 0, 1, 0], [-1j * np.exp(1j * beta) * s, 0, 0, c]],
        dtype=np.complex128,
    )
    return _gate("xx_minus_yy", 2, m, False, [theta, beta])


def _basis_permutation(num_qubits: int, mapping: dict[int, int], name: str) -> Gate:
    dim = 2**num_qubits
    m = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(dim):
        m[mapping.get(i, i), i] = 1
    return _gate(name, num_qubits, m, False)


CCXGate = _basis_permutation(3, {3: 7, 7: 3}, "ccx")
ToffoliGate = _gate("toffoli", 3, CCXGate.matrix, False)
CCZGate = _gate("ccz", 3, np.diag([1, 1, 1, 1, 1, 1, 1, -1]), False)
CSwapGate = _basis_permutation(3, {3: 5, 5: 3}, "cswap")
FredkinGate = _gate("fredkin", 3, CSwapGate.matrix, False)
MCXGate = _gate("mcx", 3, CCXGate.matrix, False)
