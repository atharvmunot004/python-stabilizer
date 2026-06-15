"""
Ancilla qubit management and parity check primitives.

Parity checks use a reusable |0> ancilla. Mixed Pauli measurements are reduced
to Z-parity measurements by local basis rotations on the data qubits.
"""
from __future__ import annotations

from typing import Dict, List

from .tableau import StabilizerState


def _validate_data_qubits(state: StabilizerState, ancilla: int, data_qubits: List[int]) -> None:
    state._check_qubit(ancilla, "ancilla")
    for index, qubit in enumerate(data_qubits):
        state._check_qubit(qubit, f"data_qubits[{index}]")
        if qubit == ancilla:
            raise ValueError("ancilla cannot also be a data qubit")


def _force_ancilla_zero(state: StabilizerState, ancilla: int) -> None:
    """
    Canonicalize a measured/reset ancilla as a product |0> qubit.

    Deterministic measurements can leave equivalent tableau rows with ancilla
    support. Once the caller has measured and reset the ancilla, it is safe to
    replace its row pair by +X_a and +Z_a and clear its column elsewhere.
    """
    n = state.n
    for row in range(2 * n):
        state.x_mat[row][ancilla] = 0
        state.z_mat[row][ancilla] = 0

    for col in range(n):
        state.x_mat[ancilla][col] = 0
        state.z_mat[ancilla][col] = 0
        state.x_mat[n + ancilla][col] = 0
        state.z_mat[n + ancilla][col] = 0

    state.x_mat[ancilla][ancilla] = 1
    state.z_mat[n + ancilla][ancilla] = 1
    state.r_phase[ancilla] = 0
    state.r_phase[n + ancilla] = 0


def _z_parity_no_reset(
    state: StabilizerState, ancilla: int, data_qubits: List[int]
) -> int:
    for data_qubit in data_qubits:
        state.cnot(data_qubit, ancilla)
    outcome = state.measure_z(ancilla)
    state.reset_z(ancilla)
    _force_ancilla_zero(state, ancilla)
    return outcome


def x_parity_check(
    state: StabilizerState,
    ancilla: int,
    data_qubits: List[int],
) -> int:
    """Measure the X-parity operator on data_qubits using ancilla."""
    _validate_data_qubits(state, ancilla, data_qubits)
    for data_qubit in data_qubits:
        state.h(data_qubit)
    outcome = _z_parity_no_reset(state, ancilla, data_qubits)
    for data_qubit in reversed(data_qubits):
        state.h(data_qubit)
    return outcome


def z_parity_check(
    state: StabilizerState,
    ancilla: int,
    data_qubits: List[int],
) -> int:
    """Measure the Z-parity operator on data_qubits using ancilla."""
    _validate_data_qubits(state, ancilla, data_qubits)
    return _z_parity_no_reset(state, ancilla, data_qubits)


def y_parity_check(
    state: StabilizerState,
    ancilla: int,
    data_qubits: List[int],
) -> int:
    """Measure the Y-parity operator on data_qubits using ancilla."""
    _validate_data_qubits(state, ancilla, data_qubits)
    for data_qubit in data_qubits:
        state.sdg(data_qubit)
        state.h(data_qubit)
    outcome = _z_parity_no_reset(state, ancilla, data_qubits)
    for data_qubit in reversed(data_qubits):
        state.h(data_qubit)
        state.s(data_qubit)
    return outcome


def mixed_parity_check(
    state: StabilizerState,
    ancilla: int,
    data_qubits: List[int],
    pauli_types: List[str],
) -> int:
    """
    Measure a mixed Pauli operator over data_qubits.

    Pauli types are one of X, Y, Z, or I. Data qubits are rotated so each
    non-identity factor is measured as a Z factor through the ancilla.
    """
    if len(data_qubits) != len(pauli_types):
        raise ValueError(
            f"data_qubits length {len(data_qubits)} != "
            f"pauli_types length {len(pauli_types)}"
        )
    _validate_data_qubits(state, ancilla, data_qubits)

    active_qubits: List[int] = []
    rotations: List[tuple[int, str]] = []
    for data_qubit, pauli_type in zip(data_qubits, pauli_types):
        pauli = pauli_type.upper()
        if pauli == "I":
            continue
        if pauli == "X":
            state.h(data_qubit)
            rotations.append((data_qubit, "X"))
        elif pauli == "Y":
            state.sdg(data_qubit)
            state.h(data_qubit)
            rotations.append((data_qubit, "Y"))
        elif pauli == "Z":
            rotations.append((data_qubit, "Z"))
        else:
            raise ValueError(f"Unknown Pauli type {pauli_type!r}. Must be X, Y, Z, or I.")
        active_qubits.append(data_qubit)

    outcome = _z_parity_no_reset(state, ancilla, active_qubits)

    for data_qubit, pauli in reversed(rotations):
        if pauli == "X":
            state.h(data_qubit)
        elif pauli == "Y":
            state.h(data_qubit)
            state.s(data_qubit)

    return outcome


class AncillaRegister:
    """
    Manages a named pool of ancilla qubits appended to a data state.

    The state is modified in place by appending one |0> qubit per name.
    Ancillas are reset after every parity check and can be reused.
    """

    def __init__(self, state: StabilizerState, names: List[str]):
        if not names:
            raise ValueError("names must be a non-empty list of strings")
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate ancilla names: {names}")

        self.state = state
        self.n_data = state.n
        self.ancilla_indices: Dict[str, int] = {}

        for name in names:
            index = state.n
            state.add_ancilla_zero()
            self.ancilla_indices[name] = index

    def _get(self, name: str) -> int:
        if name not in self.ancilla_indices:
            raise KeyError(
                f"Unknown ancilla {name!r}. Available: {list(self.ancilla_indices)}"
            )
        return self.ancilla_indices[name]

    def x_parity(self, ancilla_name: str, data_qubits: List[int]) -> int:
        return x_parity_check(self.state, self._get(ancilla_name), data_qubits)

    def z_parity(self, ancilla_name: str, data_qubits: List[int]) -> int:
        return z_parity_check(self.state, self._get(ancilla_name), data_qubits)

    def y_parity(self, ancilla_name: str, data_qubits: List[int]) -> int:
        return y_parity_check(self.state, self._get(ancilla_name), data_qubits)

    def mixed_parity(
        self,
        ancilla_name: str,
        data_qubits: List[int],
        pauli_types: List[str],
    ) -> int:
        return mixed_parity_check(
            self.state, self._get(ancilla_name), data_qubits, pauli_types
        )

    def n_ancillas(self) -> int:
        return len(self.ancilla_indices)

