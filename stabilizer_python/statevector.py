from __future__ import annotations

import random
import warnings
from typing import Dict

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - exercised only without numpy installed
    raise ImportError("statevector simulation requires numpy") from exc

from .gate import Gate
from .tableau import StabilizerState


class Statevector:
    """Dense statevector backend using Qiskit little-endian qubit indexing."""

    def __init__(self, n: int, data: np.ndarray | None = None):
        """Create an n-qubit statevector, defaulting to |0...0>."""
        if n <= 0:
            raise ValueError("n must be >= 1")
        self.n = n
        dim = 2**n
        if data is None:
            self.data = np.zeros(dim, dtype=np.complex128)
            self.data[0] = 1.0
        else:
            arr = np.asarray(data, dtype=np.complex128)
            if arr.shape != (dim,):
                raise ValueError("data length must be 2**n")
            self.data = arr.copy()

    def apply_gate(self, gate: Gate, qubits: list[int]) -> None:
        """Apply a gate to the listed qubits in place."""
        if len(qubits) != gate.num_qubits:
            raise ValueError("qubit count does not match gate")
        if len(set(qubits)) != len(qubits):
            raise ValueError("qubits must be distinct")
        for qubit in qubits:
            if qubit < 0 or qubit >= self.n:
                raise IndexError("qubit index out of range")
        if self.n > 10:
            warnings.warn("statevector apply_gate builds a dense 2^n x 2^n matrix", RuntimeWarning)

        dim = 2**self.n
        full = np.zeros((dim, dim), dtype=np.complex128)
        for col in range(dim):
            local_col = self._local_index(col, qubits)
            cleared = self._clear_qubits(col, qubits)
            for local_row in range(2**gate.num_qubits):
                row = self._set_local_index(cleared, qubits, local_row)
                full[row, col] = gate.matrix[local_row, local_col]
        self.data = full @ self.data

    def measure_z(self, qubit: int) -> int:
        """Measure a qubit in the Z basis, collapse the vector, and return 0 or 1."""
        if qubit < 0 or qubit >= self.n:
            raise IndexError("qubit index out of range")
        probs = self.probabilities()
        prob_one = float(sum(probs[i] for i in range(2**self.n) if (i >> qubit) & 1))
        outcome = 1 if random.random() < prob_one else 0
        for i in range(2**self.n):
            if ((i >> qubit) & 1) != outcome:
                self.data[i] = 0.0
        norm = np.linalg.norm(self.data)
        if norm > 0.0:
            self.data = self.data / norm
        return outcome

    def probabilities(self) -> np.ndarray:
        """Return computational-basis probabilities."""
        return np.abs(self.data) ** 2

    def inner_product(self, other: "Statevector") -> complex:
        """Return the inner product <self|other>."""
        if self.n != other.n:
            raise ValueError("statevectors must have the same number of qubits")
        return complex(np.vdot(self.data, other.data))

    def to_dict(self, tol: float = 1e-10) -> Dict[str, complex]:
        """Return nonzero amplitudes keyed by computational bitstring."""
        out: Dict[str, complex] = {}
        for i, amp in enumerate(self.data):
            if abs(amp) > tol:
                out[format(i, "0{}b".format(self.n))] = complex(amp)
        return out

    def _local_index(self, index: int, qubits: list[int]) -> int:
        local = 0
        for pos, qubit in enumerate(qubits):
            local |= ((index >> qubit) & 1) << pos
        return local

    def _clear_qubits(self, index: int, qubits: list[int]) -> int:
        out = index
        for qubit in qubits:
            out &= ~(1 << qubit)
        return out

    def _set_local_index(self, index: int, qubits: list[int], local: int) -> int:
        out = index
        for pos, qubit in enumerate(qubits):
            if (local >> pos) & 1:
                out |= 1 << qubit
        return out


def tableau_to_statevector(state: StabilizerState) -> Statevector:
    """Convert a stabilizer tableau to the unique represented statevector."""
    dim = 2**state.n
    data = np.ones(dim, dtype=np.complex128) / np.sqrt(dim)
    data = _project_all_generators(state, data)
    if np.linalg.norm(data) <= 1e-12:
        for i in range(dim):
            seed = np.zeros(dim, dtype=np.complex128)
            seed[i] = 1.0
            data = _project_all_generators(state, seed)
            if np.linalg.norm(data) > 1e-12:
                break
    norm = np.linalg.norm(data)
    if norm <= 1e-12:
        raise ValueError("could not recover statevector from tableau")
    return Statevector(state.n, data / norm)


def _project_all_generators(state: StabilizerState, data: np.ndarray) -> np.ndarray:
    out = data.copy()
    dim = 2**state.n
    ident = np.eye(dim, dtype=np.complex128)
    for phase, x_row, z_row in state.stabilizer_generators():
        pauli = _pauli_matrix(state.n, x_row, z_row)
        sign = -1.0 if phase else 1.0
        out = ((ident + sign * pauli) / 2.0) @ out
        norm = np.linalg.norm(out)
        if norm <= 1e-12:
            return out
        out = out / norm
    return out


def _pauli_matrix(n: int, x_row: list[int], z_row: list[int]) -> np.ndarray:
    single = {
        (0, 0): np.eye(2, dtype=np.complex128),
        (1, 0): np.array([[0, 1], [1, 0]], dtype=np.complex128),
        (0, 1): np.array([[1, 0], [0, -1]], dtype=np.complex128),
        (1, 1): np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
    }
    out = np.array([[1]], dtype=np.complex128)
    for qubit in reversed(range(n)):
        out = np.kron(out, single[(x_row[qubit], z_row[qubit])])
    return out
