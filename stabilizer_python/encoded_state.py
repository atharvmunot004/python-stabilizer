"""
EncodedState -- logical operator tracking for stabilizer codes.

Wraps a StabilizerState with knowledge of the logical X and Z operators for
each logical qubit, enabling non-destructive logical observable readout,
logical-error detection, logical Pauli application, and code membership checks.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .tableau import StabilizerState


def _parse_pauli_string(s: str) -> Tuple[int, List[int], List[int]]:
    """
    Parse a signed Pauli string into (phase_bit, x_row, z_row).
    """
    original = s
    s = s.strip()
    if not s:
        raise ValueError("Pauli string cannot be empty")

    if s[0] in ("+", "-"):
        phase_bit = 1 if s[0] == "-" else 0
        s = s[1:]
    else:
        phase_bit = 0

    if not s:
        raise ValueError("Pauli string cannot contain only a sign")

    x_row: List[int] = []
    z_row: List[int] = []
    for ch in s.upper():
        if ch == "I":
            x_row.append(0)
            z_row.append(0)
        elif ch == "X":
            x_row.append(1)
            z_row.append(0)
        elif ch == "Y":
            x_row.append(1)
            z_row.append(1)
        elif ch == "Z":
            x_row.append(0)
            z_row.append(1)
        else:
            raise ValueError(f"Invalid Pauli character {ch!r} in string {original!r}")
    return phase_bit, x_row, z_row


def _pauli_string_to_str(phase_bit: int, x_row: List[int], z_row: List[int]) -> str:
    """Convert (phase_bit, x_row, z_row) back to a signed Pauli string."""
    sign = "-" if phase_bit else "+"
    chars: List[str] = []
    for xb, zb in zip(x_row, z_row):
        if xb == 0 and zb == 0:
            chars.append("I")
        elif xb == 1 and zb == 0:
            chars.append("X")
        elif xb == 1 and zb == 1:
            chars.append("Y")
        else:
            chars.append("Z")
    return sign + "".join(chars)


def _symplectic_inner_product(
    x_a: List[int],
    z_a: List[int],
    x_b: List[int],
    z_b: List[int],
) -> int:
    """
    Compute the symplectic inner product of two Pauli operators over GF(2).
    """
    result = 0
    for xa, za, xb, zb in zip(x_a, z_a, x_b, z_b):
        result ^= (xa & zb) ^ (za & xb)
    return result


def _pauli_sign_in_stabilizer_group(
    state: StabilizerState,
    x_op: List[int],
    z_op: List[int],
) -> Optional[int]:
    """
    Return the sign of a Pauli operator if it is in the stabilizer group.

    Returns 0 for +P, 1 for -P, and None if P is not in the stabilizer group.
    """
    n = state.n
    if len(x_op) != n or len(z_op) != n:
        raise ValueError("Pauli operator length must match state.n")

    for r in range(n, 2 * n):
        if _symplectic_inner_product(x_op, z_op, state.x_mat[r], state.z_mat[r]):
            return None

    target = x_op[:] + z_op[:]
    rows = [state.x_mat[n + i][:] + state.z_mat[n + i][:] for i in range(n)]

    try:
        solution = state._solve_stabilizer_product(rows, target)
    except ValueError:
        return None

    work = state.copy()
    for j in range(n):
        work.x_mat[0][j] = 0
        work.z_mat[0][j] = 0
    work.r_phase[0] = 0

    for i, selected in enumerate(solution):
        if selected:
            work._rowmult(0, n + i)

    if work.x_mat[0] != x_op or work.z_mat[0] != z_op:
        return None
    return work.r_phase[0]


def _anticommutes_with_any_stabilizer(
    state: StabilizerState, x_op: List[int], z_op: List[int]
) -> bool:
    for r in range(state.n, 2 * state.n):
        if _symplectic_inner_product(x_op, z_op, state.x_mat[r], state.z_mat[r]):
            return True
    return False


class EncodedState:
    """
    A StabilizerState with tracked logical operators.

    The wrapper keeps a small logical frame: when logical Pauli gates are applied
    through this object, the expected logical eigenvalues are updated as well as
    the physical state. Residual-error checks compare the current physical
    logical signs against that frame, so intentional logical gates are not
    reported as errors.
    """

    def __init__(
        self,
        state: StabilizerState,
        code,
        *,
        code_name: str = "",
    ):
        self.physical = state
        self.k: int = code.k
        self.logical_xs: List[str] = [code.logical_x(i) for i in range(code.k)]
        self.logical_zs: List[str] = [code.logical_z(i) for i in range(code.k)]
        self._check_operators: List[str] = [
            g.lstrip("+-") for g in getattr(code, "generators", [])
        ]
        self.code_name: str = code_name or getattr(code, "name", "")
        self._expected_x: List[Optional[int]] = [
            self.logical_x_eigenvalue(i) for i in range(self.k)
        ]
        self._expected_z: List[Optional[int]] = [
            self.logical_z_eigenvalue(i) for i in range(self.k)
        ]

    @classmethod
    def from_logical_ops(
        cls,
        state: StabilizerState,
        logical_xs: List[str],
        logical_zs: List[str],
        check_operators: Optional[List[str]] = None,
        code_name: str = "",
    ) -> "EncodedState":
        """
        Construct an EncodedState directly from logical operator strings.
        """
        if len(logical_xs) != len(logical_zs):
            raise ValueError(
                f"len(logical_xs)={len(logical_xs)} != "
                f"len(logical_zs)={len(logical_zs)}"
            )

        enc = cls.__new__(cls)
        enc.physical = state
        enc.k = len(logical_xs)
        enc.logical_xs = list(logical_xs)
        enc.logical_zs = list(logical_zs)
        enc._check_operators = list(check_operators) if check_operators else []
        enc.code_name = code_name
        enc._expected_x = [enc.logical_x_eigenvalue(i) for i in range(enc.k)]
        enc._expected_z = [enc.logical_z_eigenvalue(i) for i in range(enc.k)]
        return enc

    def logical_z_eigenvalue(self, logical_qubit: int = 0) -> Optional[int]:
        """
        Read the eigenvalue of logical Z without measuring any physical qubit.
        """
        self._check_logical_qubit(logical_qubit)
        _, x_op, z_op = _parse_pauli_string(self.logical_zs[logical_qubit])
        sign_bit = _pauli_sign_in_stabilizer_group(self.physical, x_op, z_op)
        if sign_bit is None:
            return None
        return -1 if sign_bit else +1

    def logical_x_eigenvalue(self, logical_qubit: int = 0) -> Optional[int]:
        """
        Read the eigenvalue of logical X without measuring any physical qubit.
        """
        self._check_logical_qubit(logical_qubit)
        _, x_op, z_op = _parse_pauli_string(self.logical_xs[logical_qubit])
        sign_bit = _pauli_sign_in_stabilizer_group(self.physical, x_op, z_op)
        if sign_bit is None:
            return None
        return -1 if sign_bit else +1

    def measure_logical_z(self, logical_qubit: int = 0) -> int:
        """Return logical Z readout as 0 for +1 and 1 for -1."""
        eigenvalue = self.logical_z_eigenvalue(logical_qubit)
        if eigenvalue is None:
            raise ValueError(
                f"Logical Z eigenvalue for qubit {logical_qubit} is not determined."
            )
        return 0 if eigenvalue == +1 else 1

    def measure_logical_x(self, logical_qubit: int = 0) -> int:
        """Return logical X readout as 0 for +1 and 1 for -1."""
        eigenvalue = self.logical_x_eigenvalue(logical_qubit)
        if eigenvalue is None:
            raise ValueError(
                f"Logical X eigenvalue for qubit {logical_qubit} is not determined."
            )
        return 0 if eigenvalue == +1 else 1

    def has_logical_x_error(self, logical_qubit: int = 0) -> bool:
        """
        Check whether the observed logical Z sign differs from the tracked frame.
        """
        self._check_logical_qubit(logical_qubit)
        _, x_op, z_op = _parse_pauli_string(self.logical_zs[logical_qubit])
        if _anticommutes_with_any_stabilizer(self.physical, x_op, z_op):
            return True
        observed = self.logical_z_eigenvalue(logical_qubit)
        expected = self._expected_z[logical_qubit]
        return expected is not None and observed is not None and observed != expected

    def has_logical_z_error(self, logical_qubit: int = 0) -> bool:
        """
        Check whether the observed logical X sign differs from the tracked frame.
        """
        self._check_logical_qubit(logical_qubit)
        _, x_op, z_op = _parse_pauli_string(self.logical_xs[logical_qubit])
        observed = self.logical_x_eigenvalue(logical_qubit)
        expected = self._expected_x[logical_qubit]
        if expected is None:
            return False
        if _anticommutes_with_any_stabilizer(self.physical, x_op, z_op):
            return True
        return observed is not None and observed != expected

    def has_logical_error(self) -> bool:
        """Return True if any tracked logical qubit has a residual logical error."""
        for i in range(self.k):
            if self.has_logical_x_error(i) or self.has_logical_z_error(i):
                return True
        return False

    def logical_error_type(self, logical_qubit: int = 0) -> str:
        """Return 'I', 'X', 'Z', or 'Y' for the tracked residual error."""
        has_x = self.has_logical_x_error(logical_qubit)
        has_z = self.has_logical_z_error(logical_qubit)
        if has_x and has_z:
            return "Y"
        if has_x:
            return "X"
        if has_z:
            return "Z"
        return "I"

    def syndrome(self) -> List[int]:
        """Extract the code syndrome, or [] if no checks were supplied."""
        if not self._check_operators:
            return []
        from .syndrome import read_syndrome

        return read_syndrome(self.physical, self._check_operators)

    def is_valid_codeword(self) -> bool:
        """Return True when all supplied code checks are satisfied."""
        return all(bit == 0 for bit in self.syndrome())

    def apply_logical_x(self, logical_qubit: int = 0) -> None:
        """Apply the physical representative of logical X."""
        self._check_logical_qubit(logical_qubit)
        self._apply_pauli_string(self.logical_xs[logical_qubit])
        if self._expected_z[logical_qubit] is not None:
            self._expected_z[logical_qubit] *= -1

    def apply_logical_z(self, logical_qubit: int = 0) -> None:
        """Apply the physical representative of logical Z."""
        self._check_logical_qubit(logical_qubit)
        self._apply_pauli_string(self.logical_zs[logical_qubit])
        if self._expected_x[logical_qubit] is not None:
            self._expected_x[logical_qubit] *= -1

    def apply_logical_y(self, logical_qubit: int = 0) -> None:
        """
        Apply logical Y as logical X followed by logical Z, dropping global phase.
        """
        self.apply_logical_x(logical_qubit)
        self.apply_logical_z(logical_qubit)

    def apply_logical_h(self, logical_qubit: int = 0) -> None:
        """
        Swap tracked logical X and Z references.

        This updates the logical frame only. It does not apply a physical
        Hadamard circuit; call it after applying an appropriate physical
        implementation if one is available for the code.
        """
        self._check_logical_qubit(logical_qubit)
        self.logical_xs[logical_qubit], self.logical_zs[logical_qubit] = (
            self.logical_zs[logical_qubit],
            self.logical_xs[logical_qubit],
        )
        self._expected_x[logical_qubit], self._expected_z[logical_qubit] = (
            self._expected_z[logical_qubit],
            self._expected_x[logical_qubit],
        )

    def logical_state_string(self, logical_qubit: int = 0) -> str:
        """Return a compact label for the logical qubit state."""
        z_eig = self.logical_z_eigenvalue(logical_qubit)
        if z_eig == +1:
            return "|0_L>"
        if z_eig == -1:
            return "|1_L>"
        x_eig = self.logical_x_eigenvalue(logical_qubit)
        if x_eig == +1:
            return "|+_L>"
        if x_eig == -1:
            return "|-_L>"
        return "|?_L>"

    def summary(self) -> str:
        """Return a human-readable summary of the encoded state."""
        lines = [
            f"EncodedState: {self.code_name or '(unnamed)'}",
            f"  n_physical={self.physical.n}, k={self.k}",
            "",
        ]
        for i in range(self.k):
            lines.append(f"  Logical qubit {i}:")
            lines.append(f"    Xbar: {self.logical_xs[i]}")
            lines.append(f"    Zbar: {self.logical_zs[i]}")
            lines.append(f"    State: {self.logical_state_string(i)}")
            lines.append(f"    Error: {self.logical_error_type(i)}")
            lines.append("")

        syndrome = self.syndrome()
        if syndrome:
            lines.append(f"  Syndrome: {syndrome}")
            lines.append(f"  Valid codeword: {self.is_valid_codeword()}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        states = [self.logical_state_string(i) for i in range(self.k)]
        return (
            f"EncodedState({self.code_name!r}, "
            f"n={self.physical.n}, k={self.k}, logical={states})"
        )

    def _check_logical_qubit(self, i: int) -> None:
        if not (0 <= i < self.k):
            raise IndexError(f"logical_qubit={i} out of range for k={self.k}")

    def _apply_pauli_string(self, pauli_str: str) -> None:
        """Apply a signed Pauli string to the physical state."""
        _, x_row, z_row = _parse_pauli_string(pauli_str)
        if len(x_row) != self.physical.n:
            raise ValueError(
                f"Pauli string length {len(x_row)} != state.n={self.physical.n}"
            )
        for q, (xb, zb) in enumerate(zip(x_row, z_row)):
            if xb == 1 and zb == 0:
                self.physical.x(q)
            elif xb == 0 and zb == 1:
                self.physical.z(q)
            elif xb == 1 and zb == 1:
                self.physical.y(q)
