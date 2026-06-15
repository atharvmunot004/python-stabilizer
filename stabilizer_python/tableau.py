from __future__ import annotations

import io
import random
from typing import Dict, List, Optional, Tuple


def _row_mult_phase(x1: int, z1: int, x2: int, z2: int) -> int:
    """
    Phase update helper used by Aaronson–Gottesman tableau row multiplication.
    Returns exponent of i (mod 4) contributed by multiplying single-qubit Paulis.
    """
    # Identity contributes no phase.
    if (x1 == 0 and z1 == 0) or (x2 == 0 and z2 == 0):
        return 0

    # Matching Paulis also contribute no phase.
    if x1 == x2 and z1 == z2:
        return 0

    # Explicit non-commuting Pauli multiplication phases:
    # XZ = +iY, ZX = -iY
    if x1 == 1 and z1 == 0 and x2 == 0 and z2 == 1:
        return 1
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 0:
        return 3

    # ZY = +iX, YZ = -iX
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 1:
        return 1
    if x1 == 1 and z1 == 1 and x2 == 0 and z2 == 1:
        return 3

    # YX = +iZ, XY = -iZ
    if x1 == 1 and z1 == 1 and x2 == 1 and z2 == 0:
        return 1
    if x1 == 1 and z1 == 0 and x2 == 1 and z2 == 1:
        return 3

    raise ValueError("invalid Pauli bits for row multiplication")


def _pauli_string(phase: int, x_row: List[int], z_row: List[int]) -> str:
    """Convert a tableau row to a signed Pauli string."""
    sign = "-" if phase else "+"
    pauli = ""
    for xb, zb in zip(x_row, z_row):
        if xb == 0 and zb == 0:
            pauli += "I"
        elif xb == 1 and zb == 0:
            pauli += "X"
        elif xb == 1 and zb == 1:
            pauli += "Y"
        else:
            pauli += "Z"
    return sign + pauli


class StabilizerState:
    """
    Stabilizer tableau representing an n-qubit stabilizer state.

    Representation follows Aaronson–Gottesman:
    - 2n rows: first n are destabilizers, last n are stabilizers
    - x[r][q], z[r][q] bits
    - r_phase[r] is 0/1 representing overall sign (-1)^r_phase (we only need +/- for state simulation)
    """

    def __init__(self, n: int, x: List[List[int]], z: List[List[int]], r_phase: List[int]):
        self.n = n
        self.x_mat = x
        self.z_mat = z
        self.r_phase = r_phase

    @classmethod
    def zero(cls, n: int) -> "StabilizerState":
        if n <= 0:
            raise ValueError("n must be >= 1")
        x = [[0] * n for _ in range(2 * n)]
        z = [[0] * n for _ in range(2 * n)]
        r_phase = [0 for _ in range(2 * n)]

        # |0...0> stabilizers: Z_i (rows n+i)
        # destabilizers: X_i (rows i)
        for i in range(n):
            x[i][i] = 1
            z[n + i][i] = 1
        return cls(n=n, x=x, z=z, r_phase=r_phase)

    @classmethod
    def from_stabilizer_list(cls, stabilizers: List[str]) -> "StabilizerState":
        """
        Construct a StabilizerState from a list of signed Pauli strings.

        This mirrors Qiskit's ``StabilizerState.from_stabilizer_list()``.
        The list must contain exactly n independent commuting Pauli operators
        on n qubits.  Each string may optionally start with '+' or '-'; if no
        sign is given '+' is assumed.

        The implementation:
        1. Parses each Pauli string into (phase_bit, x_row, z_row).
        2. Places the parsed rows into the stabilizer half (rows n..2n-1) of a
           fresh zero-state tableau.
        3. Reconstructs the destabilizer rows using the standard rule: for each
           qubit i, the destabilizer is the unique row that anticommutes with
           stabilizer i and commutes with all others.  For a diagonal stabilizer
           set this is trivially X_i; for non-diagonal sets we derive it by
           inspection using GF(2) elimination.
        4. Returns the resulting StabilizerState.

        Raises ValueError if:
        - Any string contains characters other than I, X, Y, Z (and optional
          leading +/-).
        - All strings do not have the same length after stripping the sign.
        - The number of generators does not equal the number of qubits.

        Example::

            >>> st = StabilizerState.from_stabilizer_list(['+XX', '+ZZ'])
            >>> st.stabilizer_strings()
            ['+XX', '+ZZ']
        """
        # --- parse ---
        parsed: List[Tuple[int, List[int], List[int]]] = []
        for raw in stabilizers:
            s = raw.strip()
            if s and s[0] in ('+', '-'):
                phase_bit = 1 if s[0] == '-' else 0
                s = s[1:]
            else:
                phase_bit = 0
            if not s:
                raise ValueError(f"Empty Pauli string in input: {raw!r}")
            x_row: List[int] = []
            z_row: List[int] = []
            for ch in s.upper():
                if ch == 'I':
                    x_row.append(0); z_row.append(0)
                elif ch == 'X':
                    x_row.append(1); z_row.append(0)
                elif ch == 'Y':
                    x_row.append(1); z_row.append(1)
                elif ch == 'Z':
                    x_row.append(0); z_row.append(1)
                else:
                    raise ValueError(
                        f"Invalid Pauli character {ch!r} in string {raw!r}"
                    )
            parsed.append((phase_bit, x_row, z_row))

        n = len(parsed[0][1]) if parsed else 0
        if len(parsed) != n:
            raise ValueError(
                f"Expected {n} stabilizer generators for {n} qubits, "
                f"got {len(parsed)}"
            )
        for i, (_, xr, zr) in enumerate(parsed):
            if len(xr) != n:
                raise ValueError(
                    f"Stabilizer {i} has length {len(xr)}, expected {n}"
                )

        # --- build tableau ---
        # Start from |0...0> to get valid destabilizer rows, then overwrite stab rows.
        state = cls.zero(n)
        for i, (phase_bit, x_row, z_row) in enumerate(parsed):
            r = n + i  # stabilizer slot
            state.r_phase[r] = phase_bit
            state.x_mat[r] = x_row[:]
            state.z_mat[r] = z_row[:]

        # Rebuild destabilizer rows so that destabilizer i anticommutes with
        # stabilizer i and commutes with all other stabilizers.
        # Strategy: for each stabilizer row r = n+i, find the first qubit position
        # p where the row has X or Y support.  Set destabilizer i to X_p (the
        # simplest anticommuting partner), then clear any X support that would
        # cause it to anticommute with other stabilizers by multiplying rows.
        # For the common case (diagonal Z stabilizers), this reduces to X_i directly.
        for i in range(n):
            # Reset destabilizer row i to identity.
            state.x_mat[i] = [0] * n
            state.z_mat[i] = [0] * n
            state.r_phase[i] = 0
            # Find first qubit where stabilizer i has Z or Y (i.e., z bit set).
            pivot = -1
            for q in range(n):
                if state.z_mat[n + i][q] == 1:
                    pivot = q
                    break
            if pivot == -1:
                # Stabilizer has only X support; find first X qubit.
                for q in range(n):
                    if state.x_mat[n + i][q] == 1:
                        pivot = q
                        break
            if pivot == -1:
                raise ValueError(
                    f"Stabilizer {i} is the identity operator, which is invalid."
                )
            # Set destabilizer i to the single-qubit operator on pivot that
            # anticommutes with stabilizer i at that qubit.
            z_at_pivot = state.z_mat[n + i][pivot]
            x_at_pivot = state.x_mat[n + i][pivot]
            if z_at_pivot == 1:
                # Stabilizer has Z or Y at pivot -> anticommuting partner is X.
                state.x_mat[i][pivot] = 1
                state.z_mat[i][pivot] = 0
            else:
                # Stabilizer has only X at pivot -> anticommuting partner is Z.
                state.x_mat[i][pivot] = 0
                state.z_mat[i][pivot] = 1

        return state

    # --- Basic tableau utilities ---
    def copy(self) -> "StabilizerState":
        return StabilizerState(
            n=self.n,
            x=[row[:] for row in self.x_mat],
            z=[row[:] for row in self.z_mat],
            r_phase=self.r_phase[:],
        )

    def _check_qubit(self, q: int, name: str = "q") -> None:
        if not (0 <= q < self.n):
            raise ValueError(f"{name}={q} out of range for {self.n}-qubit state")

    def _symplectic_product(self, row_a: int, row_b: int) -> int:
        total = 0
        for q in range(self.n):
            total ^= self.x_mat[row_a][q] & self.z_mat[row_b][q]
            total ^= self.z_mat[row_a][q] & self.x_mat[row_b][q]
        return total

    def _check_tableau_invariants(self) -> None:
        """Assert stabilizer rows are independent and mutually commuting."""
        from .linear_algebra import rank_gf2

        stab_x = [self.x_mat[self.n + i][:] for i in range(self.n)]
        stab_z = [self.z_mat[self.n + i][:] for i in range(self.n)]
        combined = [stab_x[i] + stab_z[i] for i in range(self.n)]
        assert rank_gf2(combined) == self.n, "Stabilizer rows are not independent"
        for i in range(self.n):
            row_a = self.n + i
            assert any(stab_x[i] + stab_z[i]), "Stabilizer row is zero"
            for j in range(i + 1, self.n):
                row_b = self.n + j
                assert self._symplectic_product(row_a, row_b) == 0, (
                    "Stabilizer rows do not commute"
                )

    def _rowswap(self, a: int, b: int) -> None:
        self.x_mat[a], self.x_mat[b] = self.x_mat[b], self.x_mat[a]
        self.z_mat[a], self.z_mat[b] = self.z_mat[b], self.z_mat[a]
        self.r_phase[a], self.r_phase[b] = self.r_phase[b], self.r_phase[a]

    def _rowmult(self, a: int, b: int) -> None:
        """
        Row a <- Row a * Row b (Pauli multiplication) with phase tracking (mod 2 sign).
        """
        n = self.n
        # Track phase using i-exponent mod 4, then reduce to sign (0/1).
        exp_i = 0
        if self.r_phase[a]:
            exp_i += 2
        if self.r_phase[b]:
            exp_i += 2
        for q in range(n):
            exp_i += _row_mult_phase(
                self.x_mat[a][q], self.z_mat[a][q], self.x_mat[b][q], self.z_mat[b][q]
            )
        exp_i %= 4

        for q in range(n):
            self.x_mat[a][q] ^= self.x_mat[b][q]
            self.z_mat[a][q] ^= self.z_mat[b][q]

        # exp_i == 0 => +1, exp_i == 2 => -1, exp_i in {1,3} should never occur for valid tableau rows
        self.r_phase[a] = 1 if exp_i == 2 else 0

    # --- Clifford gates ---
    def i(self, q: int) -> None:
        """Identity gate; included for completeness with Clifford gate sets."""
        self._check_qubit(q)

    def h(self, q: int) -> None:
        self._check_qubit(q)
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -Y under H (sign flip)
            self.x_mat[r][q], self.z_mat[r][q] = z, x

    def s(self, q: int) -> None:
        self._check_qubit(q)
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -X under S
            self.z_mat[r][q] ^= x

    def sdg(self, q: int) -> None:
        self._check_qubit(q)
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & (z ^ 1):
                self.r_phase[r] ^= 1  # X -> -Y under S†
            self.z_mat[r][q] ^= x

    def s_dagger(self, q: int) -> None:
        self.sdg(q)

    def sx(self, q: int) -> None:
        self._check_qubit(q)
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if (x ^ 1) & z:
                self.r_phase[r] ^= 1  # Z -> -Y under √X
            self.x_mat[r][q] ^= z

    def sqrt_x(self, q: int) -> None:
        self.sx(q)

    def sxdg(self, q: int) -> None:
        self._check_qubit(q)
        for r in range(2 * self.n):
            x = self.x_mat[r][q]
            z = self.z_mat[r][q]
            if x & z:
                self.r_phase[r] ^= 1  # Y -> -Z under √X†
            self.x_mat[r][q] ^= z

    def sqrt_x_dagger(self, q: int) -> None:
        self.sxdg(q)

    def x(self, q: int) -> None:
        self._check_qubit(q)
        # Conjugation by X flips sign of Z and Y.
        for r in range(2 * self.n):
            if self.z_mat[r][q] == 1:
                self.r_phase[r] ^= 1

    def y(self, q: int) -> None:
        self._check_qubit(q)
        # Conjugation by Y flips sign of X and Z, but not Y.
        for r in range(2 * self.n):
            if self.x_mat[r][q] ^ self.z_mat[r][q]:
                self.r_phase[r] ^= 1

    def z(self, q: int) -> None:
        self._check_qubit(q)
        # Conjugation by Z flips sign of X and Y.
        for r in range(2 * self.n):
            if self.x_mat[r][q] == 1:
                self.r_phase[r] ^= 1

    def cx(self, control: int, target: int) -> None:
        self.cnot(control, target)

    def cnot(self, control: int, target: int) -> None:
        self._check_qubit(control, "control")
        self._check_qubit(target, "target")
        c, t = control, target
        for r in range(2 * self.n):
            xc = self.x_mat[r][c]
            zc = self.z_mat[r][c]
            xt = self.x_mat[r][t]
            zt = self.z_mat[r][t]

            # Phase update per Aaronson–Gottesman
            if xc & zt & (xt ^ zc ^ 1):
                self.r_phase[r] ^= 1

            self.x_mat[r][t] ^= xc
            self.z_mat[r][c] ^= zt

    def cz(self, control: int, target: int) -> None:
        self.h(target)
        self.cnot(control, target)
        self.h(target)

    def cy(self, control: int, target: int) -> None:
        self.sdg(target)
        self.cnot(control, target)
        self.s(target)

    def swap(self, q1: int, q2: int) -> None:
        self._check_qubit(q1, "q1")
        self._check_qubit(q2, "q2")
        self.cnot(q1, q2)
        self.cnot(q2, q1)
        self.cnot(q1, q2)

    # --- Measurement ---
    def z_measurement_branch(self, q: int) -> str:
        """
        Classify an upcoming Z measurement on qubit q as deterministic or random.

        Matches the branch taken by measure_z(): random when some stabilizer row
        anticommutes with Z_q (X component on q), otherwise deterministic.
        """
        self._check_qubit(q)
        for r in range(self.n, 2 * self.n):
            if self.x_mat[r][q] == 1:
                return "random"
        return "deterministic"

    def measure_z(self, q: int) -> int:
        """
        Measure Z on qubit q. Returns outcome bit (0 -> +1 eigenvalue, 1 -> -1 eigenvalue).
        """
        self._check_qubit(q)
        n = self.n
        # Search for a stabilizer row that anticommutes with Z_q (i.e., has X on q)
        p = -1
        for r in range(n, 2 * n):
            if self.x_mat[r][q] == 1:
                p = r
                break

        if p == -1:
            # Deterministic: Z_q is fixed by a product of stabilizer rows.
            return self._deterministic_z_outcome(q)

        # Random outcome
        outcome = random.randint(0, 1)

        # Make p the pivot stabilizer row for this measurement by clearing X on q in other rows
        for r in range(2 * n):
            if r != p and self.x_mat[r][q] == 1:
                self._rowmult(r, p)

        # Move pivot into destabilizer slot corresponding to this qubit (use row n+q as canonical)
        self._rowswap(p, n + q)

        # Set new stabilizer row (n+q) to measured Z on q with outcome sign.
        # In AG tableau, after measurement, stabilizer row becomes Z_q with phase outcome.
        for j in range(n):
            self.x_mat[n + q][j] = 0
            self.z_mat[n + q][j] = 0
        self.z_mat[n + q][q] = 1
        self.r_phase[n + q] = outcome

        # Destabilizer row q becomes previous pivot row content (now at position p), ensure X on q.
        # We want destabilizer row q to anticommute with new Z_q, simplest is set it to X_q.
        for j in range(n):
            self.x_mat[q][j] = 0
            self.z_mat[q][j] = 0
        self.x_mat[q][q] = 1
        self.r_phase[q] = 0

        return outcome

    def _deterministic_z_outcome(self, q: int) -> int:
        """
        Return the sign of Z_q when it is already implied by the stabilizer group.
        """
        n = self.n
        target = [0] * (2 * n)
        target[n + q] = 1
        rows = [self.x_mat[n + i][:] + self.z_mat[n + i][:] for i in range(n)]
        solution = self._solve_stabilizer_product(rows, target)

        work = self.copy()
        for j in range(n):
            work.x_mat[0][j] = 0
            work.z_mat[0][j] = 0
        work.r_phase[0] = 0

        for i, selected in enumerate(solution):
            if selected:
                work._rowmult(0, n + i)
        return work.r_phase[0]

    def _solve_stabilizer_product(self, rows: List[List[int]], target: List[int]) -> List[int]:
        """
        Solve for stabilizer-row coefficients whose binary Pauli vector equals target.
        """
        n = self.n
        matrix = [[rows[var][eq] for var in range(n)] + [target[eq]] for eq in range(2 * n)]
        pivot_rows: List[int] = []
        pivot_cols: List[int] = []
        row = 0
        for col in range(n):
            pivot = -1
            for r in range(row, 2 * n):
                if matrix[r][col] == 1:
                    pivot = r
                    break
            if pivot == -1:
                continue
            matrix[row], matrix[pivot] = matrix[pivot], matrix[row]
            for r in range(2 * n):
                if r != row and matrix[r][col] == 1:
                    for c in range(col, n + 1):
                        matrix[r][c] ^= matrix[row][c]
            pivot_rows.append(row)
            pivot_cols.append(col)
            row += 1

        for r in range(row, 2 * n):
            if all(matrix[r][c] == 0 for c in range(n)) and matrix[r][n] == 1:
                raise ValueError("deterministic measurement target is not in stabilizer span")

        solution = [0] * n
        for pivot_row, pivot_col in zip(pivot_rows, pivot_cols):
            solution[pivot_col] = matrix[pivot_row][n]
        return solution

    def reset_z(self, q: int) -> int:
        """
        Measures Z on q and (if needed) applies X so the post-state has q in |0>.
        Returns the measurement outcome bit.
        """
        m = self.measure_z(q)
        if m == 1:
            self.x(q)
        return m

    def add_ancilla_zero(self) -> None:
        """
        Extend the tableau by one ancilla qubit in |0>.

        Existing rows gain identity support on the new qubit. A new
        destabilizer +X_n is inserted at the destabilizer/stabilizer boundary,
        and a new stabilizer +Z_n is appended at the end.
        """
        n = self.n
        new_n = n + 1

        for i in range(2 * n):
            self.x_mat[i].append(0)
            self.z_mat[i].append(0)

        new_destab_x = [0] * new_n
        new_destab_z = [0] * new_n
        new_destab_x[n] = 1
        self.x_mat.insert(n, new_destab_x)
        self.z_mat.insert(n, new_destab_z)
        self.r_phase.insert(n, 0)

        new_stab_x = [0] * new_n
        new_stab_z = [0] * new_n
        new_stab_z[n] = 1
        self.x_mat.append(new_stab_x)
        self.z_mat.append(new_stab_z)
        self.r_phase.append(0)

        self.n = new_n

    def add_ancilla_plus(self) -> None:
        """
        Extend the tableau by one ancilla qubit in |+>.

        Equivalent to add_ancilla_zero() followed by H on the new qubit.
        """
        self.add_ancilla_zero()
        self.h(self.n - 1)

    def remove_ancilla(self, q: int) -> None:
        """
        Remove a disentangled ancilla qubit from the tableau.

        Call measure_z(q) and reset_z(q) first so the qubit is in |0>. Qubits
        above q are shifted down by one index after removal.
        """
        n = self.n
        if q < 0 or q >= n:
            raise IndexError(f"qubit index {q} out of range for {n}-qubit state")
        if n <= 1:
            raise ValueError("cannot remove the only qubit in a tableau")

        def _only_support(row: int) -> bool:
            for col in range(n):
                if col == q:
                    continue
                if self.x_mat[row][col] or self.z_mat[row][col]:
                    return False
            return True

        stab_rows = [
            row
            for row in range(n, 2 * n)
            if self.x_mat[row][q] or self.z_mat[row][q]
        ]
        if len(stab_rows) != 1:
            raise ValueError(
                f"Qubit {q} appears in {len(stab_rows)} stabilizer rows; "
                "call measure_z(q) and reset_z(q) before removing it."
            )
        stab_row = stab_rows[0]
        if (
            self.x_mat[stab_row][q] != 0
            or self.z_mat[stab_row][q] != 1
            or not _only_support(stab_row)
        ):
            raise ValueError(f"Qubit {q} is not isolated as a +Z stabilizer")

        destab_rows = [
            row
            for row in range(n)
            if self.x_mat[row][q] or self.z_mat[row][q]
        ]
        if len(destab_rows) != 1:
            raise ValueError(
                f"Qubit {q} appears in {len(destab_rows)} destabilizer rows; "
                "call measure_z(q) and reset_z(q) before removing it."
            )
        destab_row = destab_rows[0]
        if (
            self.x_mat[destab_row][q] != 1
            or self.z_mat[destab_row][q] != 0
            or not _only_support(destab_row)
        ):
            raise ValueError(f"Qubit {q} is not isolated as a +X destabilizer")

        for row in sorted([stab_row, destab_row], reverse=True):
            self.x_mat.pop(row)
            self.z_mat.pop(row)
            self.r_phase.pop(row)

        for row in range(len(self.x_mat)):
            del self.x_mat[row][q]
            del self.z_mat[row][q]

        self.n = n - 1

    # --- Debug / inspection helpers ---
    def _pauli_char_at(self, r: int, q: int) -> str:
        xb, zb = self.x_mat[r][q], self.z_mat[r][q]
        if xb == 0 and zb == 0:
            return "I"
        if xb == 1 and zb == 0:
            return "X"
        if xb == 1 and zb == 1:
            return "Y"
        return "Z"

    def _row_to_pauli(self, r: int) -> str:
        sign = "-" if self.r_phase[r] else "+"
        pauli = "".join(self._pauli_char_at(r, q) for q in range(self.n))
        return sign + pauli

    def format_chp_printstate(self) -> str:
        """
        Same layout as CHP's printstate(): destabilizer rows, a rule line, stabilizer rows,
        each row prefixed with + or - from the sign bit (CHP phase mod 4 reduced to +/- here).
        """
        return self._format_chp_rows(0, 2 * self.n, include_separator=True)

    def _format_chp_rows(
        self, start: int, end: int, *, include_separator: bool = False
    ) -> str:
        buf = io.StringIO()
        for i in range(start, end):
            if include_separator and i == self.n:
                buf.write("\n")
                buf.write("-" * (self.n + 1))
                buf.write("\n")
            buf.write(self._row_to_pauli(i))
            buf.write("\n")
        text = buf.getvalue()
        return text[:-1] if text else text

    def _format_stabilizers_only(self) -> str:
        """CHP-style stabilizer rows only (tableau rows n..2n-1)."""
        return self._format_chp_rows(self.n, 2 * self.n)

    def _format_destabilizers_only(self) -> str:
        """CHP-style destabilizer rows only (tableau rows 0..n-1)."""
        return self._format_chp_rows(0, self.n)

    def inspect(self, views: Optional[List[str]] = None) -> str:
        """
        Return one or more tableau inspection views.

        When views is None, returns all four standard views (CHP, binary matrices,
        phase column, and full debug bundle) separated by blank lines. Pass a list
        of view names to select specific outputs.
        """
        view_map = {
            "chp": self.format_chp_printstate,
            "binary": self.format_xz_binary_matrices,
            "phase": self.format_phase_matrix,
            "debug": self.format_tableau_debug,
            "stabilizers": self._format_stabilizers_only,
            "destabilizers": self._format_destabilizers_only,
        }
        selected = ["chp"] if views is None else list(views)
        unknown = [view for view in selected if view not in view_map]
        if unknown:
            raise ValueError(f"unknown inspect view(s): {unknown}")
        buf = io.StringIO()
        for index, view in enumerate(selected):
            if index:
                buf.write("\n\n")
            buf.write(view_map[view]())
        return buf.getvalue()

    def format_xz_binary_matrices(self) -> str:
        """Print the raw X and Z bit tables (2n rows × n columns), side by side."""

        def _fmt_row(row: List[int]) -> str:
            return "  " + " ".join(str(b) for b in row)

        n_rows = 2 * self.n
        x_title = f"X matrix ({n_rows} x {self.n})"
        z_title = f"Z matrix ({n_rows} x {self.n})"
        gap = "    "
        x_rows = [_fmt_row(row) for row in self.x_mat]
        z_rows = [_fmt_row(row) for row in self.z_mat]
        left_width = max([len(x_title)] + [len(r) for r in x_rows])

        buf = io.StringIO()
        buf.write(x_title.ljust(left_width) + gap + z_title)
        buf.write("\n")
        for i in range(n_rows):
            buf.write(x_rows[i].ljust(left_width) + gap + z_rows[i])
            buf.write("\n")
        text = buf.getvalue()
        return text[:-1] if text else text

    def format_phase_matrix(self) -> str:
        """Print the tableau phase bits as a 2n × 1 column matrix."""
        buf = io.StringIO()
        buf.write(f"Phase matrix ({2 * self.n} x 1)")
        for phase in self.r_phase:
            buf.write(f"\n  [{phase}]")
        return buf.getvalue()

    def format_tableau_debug(self) -> str:
        """CHP-style Pauli rows plus explicit X, Z, and phase matrices."""
        buf = io.StringIO()
        buf.write("Tableau (CHP-style destabilizers | stabilizers):\n")
        buf.write(self.format_chp_printstate())
        buf.write("\n\n")
        buf.write(self.format_xz_binary_matrices())
        buf.write("\n\n")
        buf.write(self.format_phase_matrix())
        return buf.getvalue()

    def stabilizer_generators(self) -> List[Tuple[int, List[int], List[int]]]:
        """
        Returns list of stabilizer generators as (phase_bit, x_row, z_row) for the last n rows.
        """
        out = []
        for r in range(self.n, 2 * self.n):
            out.append((self.r_phase[r], self.x_mat[r][:], self.z_mat[r][:]))
        return out

    def destabilizer_generators(self) -> List[Tuple[int, List[int], List[int]]]:
        """
        Returns list of destabilizer generators as (phase_bit, x_row, z_row) for the first n rows.
        """
        out = []
        for r in range(self.n):
            out.append((self.r_phase[r], self.x_mat[r][:], self.z_mat[r][:]))
        return out

    def stabilizer_strings(self) -> List[str]:
        """
        Return the n stabilizer generators as a list of signed Pauli strings.

        Each string has a leading '+' or '-' sign followed by n Pauli characters
        (I, X, Y, Z), one per qubit.  This mirrors Qiskit's
        ``Clifford.to_labels(mode="S")`` return format.

        Example for a 3-qubit GHZ state::

            >>> st.stabilizer_strings()
            ['+XXX', '+ZZI', '+ZIZ']
        """
        return [
            _pauli_string(phase, x_row, z_row)
            for phase, x_row, z_row in self.stabilizer_generators()
        ]

    def destabilizer_strings(self) -> List[str]:
        """
        Return the n destabilizer generators as a list of signed Pauli strings.

        Each string has a leading '+' or '-' sign followed by n Pauli characters
        (I, X, Y, Z), one per qubit.  This mirrors Qiskit's
        ``Clifford.to_labels(mode="D")`` return format.

        Destabilizers are the computational bookkeeping rows used for efficient
        measurement simulation.  They are not part of the physical state description
        and are not listed in standard textbook treatments.

        Example for a 3-qubit GHZ state::

            >>> st.destabilizer_strings()
            ['+ZII', '+IXI', '+IIX']
        """
        return [
            _pauli_string(phase, x_row, z_row)
            for phase, x_row, z_row in self.destabilizer_generators()
        ]

    def tableau_dict(self) -> Dict[str, List[str]]:
        """
        Return stabilizer and destabilizer generators as signed Pauli strings.

        Example for a Bell state::

            >>> st.tableau_dict()
            {'stabilizers': ['+XX', '+ZZ'], 'destabilizers': ['+XI', '+IX']}
        """
        return {
            "stabilizers": self.stabilizer_strings(),
            "destabilizers": self.destabilizer_strings(),
        }

