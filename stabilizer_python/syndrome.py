"""
General syndrome extraction for stabilizer codes.
"""
from __future__ import annotations

from typing import List

from .ancilla import AncillaRegister, mixed_parity_check
from .tableau import StabilizerState


def _normalise_checks(check_operators: List[str], n_data: int) -> List[str]:
    checks: List[str] = []
    for index, operator in enumerate(check_operators):
        clean = operator.strip().upper()
        if len(clean) != n_data:
            raise ValueError(
                f"Check operator {index} has length {len(clean)}, expected {n_data}."
            )
        for char in clean:
            if char not in ("I", "X", "Y", "Z"):
                raise ValueError(
                    f"Invalid character {char!r} in check operator {index}: {operator!r}"
                )
        checks.append(clean)
    return checks


def read_syndrome(
    state: StabilizerState,
    check_operators: List[str],
) -> List[int]:
    """
    Extract syndrome bits for check_operators, adding and removing one ancilla.
    """
    n_data = state.n
    checks = _normalise_checks(check_operators, n_data)

    state.add_ancilla_zero()
    ancilla = state.n - 1

    try:
        syndrome: List[int] = []
        data_qubits = list(range(n_data))
        for operator in checks:
            syndrome.append(
                mixed_parity_check(state, ancilla, data_qubits, list(operator))
            )
        return syndrome
    finally:
        state.remove_ancilla(ancilla)


class SyndromeExtractor:
    """
    Reusable syndrome extractor for a fixed set of check operators.

    Ancilla qubits are allocated once and remain part of state for the lifetime
    of the extractor.
    """

    def __init__(
        self,
        state: StabilizerState,
        check_operators: List[str],
        n_ancillas: int = 1,
    ):
        if n_ancillas <= 0:
            raise ValueError("n_ancillas must be >= 1")

        self.n_data = state.n
        self.check_operators = _normalise_checks(check_operators, self.n_data)
        self.state = state
        ancilla_names = [f"_anc{i}" for i in range(n_ancillas)]
        self.register = AncillaRegister(state, names=ancilla_names)
        self._ancilla_name = ancilla_names[0]

    def extract(self) -> List[int]:
        syndrome: List[int] = []
        data_qubits = list(range(self.n_data))
        for operator in self.check_operators:
            syndrome.append(
                self.register.mixed_parity(
                    self._ancilla_name, data_qubits, list(operator)
                )
            )
        return syndrome

    def n_checks(self) -> int:
        return len(self.check_operators)

