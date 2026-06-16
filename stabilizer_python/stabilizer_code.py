"""
General [[n, k, d]] stabilizer code class.

A stabilizer code is defined by n-k independent, commuting Pauli operators
(the stabilizer generators) on n physical qubits. It encodes k logical qubits
with distance d (the minimum weight of a non-trivial logical operator).

Usage::

    from stabilizer_python.stabilizer_code import StabilizerCode, SteaneCode

    state = SteaneCode.zero_state()
    syndrome = SteaneCode.read_syndrome(state)
    print(syndrome)   # [0, 0, 0, 0, 0, 0] -- no error
"""
from __future__ import annotations

import itertools
from typing import List, Optional, Tuple

from .linear_algebra import rank_gf2
from .syndrome import SyndromeExtractor, read_syndrome as _read_syndrome
from .tableau import StabilizerState


def _parse_pauli(s: str) -> Tuple[int, List[int], List[int]]:
    """Parse a Pauli string into (phase_bit, x_row, z_row)."""
    s = s.strip()
    if not s:
        raise ValueError("Pauli string cannot be empty")

    if s[0] in ("+", "-"):
        phase = 1 if s[0] == "-" else 0
        s = s[1:]
    else:
        phase = 0

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
            raise ValueError(f"Invalid Pauli character {ch!r}")
    return phase, x_row, z_row


def _strip_sign(s: str) -> str:
    """Remove leading + or - from a Pauli string."""
    s = s.strip()
    return s[1:] if s and s[0] in ("+", "-") else s


def _xz_to_pauli(x: int, z: int) -> str:
    if x == 0 and z == 0:
        return "I"
    if x == 1 and z == 0:
        return "X"
    if x == 1 and z == 1:
        return "Y"
    return "Z"


def _gf2_row_reduce(
    mat: List[List[int]], n_cols: int
) -> Tuple[List[List[int]], List[int]]:
    """
    Row-reduce a binary matrix over GF(2).

    Returns:
        (reduced_matrix, pivot_columns) where pivot_columns lists the column
        index of the leading 1 in each non-zero row.
    """
    m = [row[:] for row in mat]
    n_rows = len(m)
    pivot_cols: List[int] = []
    pivot_row = 0
    for col in range(n_cols):
        found = -1
        for r in range(pivot_row, n_rows):
            if m[r][col] == 1:
                found = r
                break
        if found == -1:
            continue
        m[pivot_row], m[found] = m[found], m[pivot_row]
        pivot_cols.append(col)
        for r in range(n_rows):
            if r != pivot_row and m[r][col] == 1:
                m[r] = [m[r][c] ^ m[pivot_row][c] for c in range(n_cols)]
        pivot_row += 1
        if pivot_row == n_rows:
            break
    return m, pivot_cols


def _nullspace_gf2(mat: List[List[int]], n_cols: int) -> List[List[int]]:
    """Return a basis for the nullspace of mat over GF(2)."""
    reduced, pivot_cols = _gf2_row_reduce(mat, n_cols)
    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(n_cols) if c not in pivot_set]
    basis: List[List[int]] = []

    for free_col in free_cols:
        vec = [0] * n_cols
        vec[free_col] = 1
        for row_idx in range(len(pivot_cols) - 1, -1, -1):
            pivot_col = pivot_cols[row_idx]
            value = 0
            for col in free_cols:
                if reduced[row_idx][col] and vec[col]:
                    value ^= 1
            vec[pivot_col] = value
        basis.append(vec)
    return basis


def _symplectic_product(
    x1: List[int], z1: List[int], x2: List[int], z2: List[int]
) -> int:
    total = 0
    for q in range(len(x1)):
        total ^= (x1[q] & z2[q]) ^ (z1[q] & x2[q])
    return total


def _symplectic_product_vec(a: List[int], b: List[int]) -> int:
    n = len(a) // 2
    total = 0
    for q in range(n):
        total ^= (a[q] & b[n + q]) ^ (a[n + q] & b[q])
    return total


def _vector_to_pauli(vec: List[int]) -> str:
    n = len(vec) // 2
    return "+" + "".join(_xz_to_pauli(vec[q], vec[n + q]) for q in range(n))


def _pauli_to_vector(s: str) -> List[int]:
    _, x_row, z_row = _parse_pauli(s)
    return x_row + z_row


def _is_in_span(vec: List[int], basis: List[List[int]]) -> bool:
    if not basis:
        return not any(vec)
    return rank_gf2(basis + [vec]) == rank_gf2(basis)


def _xor_into(target: List[int], source: List[int]) -> None:
    for i, value in enumerate(source):
        target[i] ^= value


def _validate_logicals(
    logicals: Optional[List[str]], k: int, n: int, label: str
) -> Optional[List[str]]:
    if logicals is None:
        return None
    if len(logicals) != k:
        raise ValueError(f"Expected {k} {label} operators, got {len(logicals)}")
    clean: List[str] = []
    for i, operator in enumerate(logicals):
        phase, x_row, _ = _parse_pauli(operator)
        body = _strip_sign(operator).upper()
        if len(body) != n:
            raise ValueError(
                f"{label} operator {i} has length {len(body)}, expected {n}"
            )
        clean.append(("-" if phase else "+") + body)
        if not any(x_row) and set(body) <= {"I"}:
            raise ValueError(f"{label} operator {i} cannot be identity")
    return clean


class StabilizerCode:
    """
    A general [[n, k, d]] stabilizer code.

    Attributes:
        n (int): Number of physical qubits.
        k (int): Number of logical qubits.
        generators (list[str]): The n-k stabilizer generators as signed Pauli
            strings (e.g. '+XZZXI'). Signs are preserved but not used for
            syndrome extraction.
        name (str): Human-readable name, e.g. 'Steane [[7,1,3]]'.
    """

    def __init__(
        self,
        n: int,
        k: int,
        generators: List[str],
        name: str = "",
        logical_xs: Optional[List[str]] = None,
        logical_zs: Optional[List[str]] = None,
    ):
        if n <= 0:
            raise ValueError("n must be >= 1")
        if not (0 <= k <= n):
            raise ValueError("k must satisfy 0 <= k <= n")
        if len(generators) != n - k:
            raise ValueError(
                f"Expected {n-k} generators for [[{n},{k}]] code, "
                f"got {len(generators)}"
            )

        clean: List[str] = []
        for i, g in enumerate(generators):
            s = g.strip()
            if not s:
                raise ValueError(f"Generator {i} is empty")
            if s[0] in ("+", "-"):
                sign = s[0]
                body = s[1:].upper()
            else:
                sign = "+"
                body = s.upper()
            if len(body) != n:
                raise ValueError(f"Generator {i} has length {len(body)}, expected {n}")
            for ch in body:
                if ch not in ("I", "X", "Y", "Z"):
                    raise ValueError(
                        f"Invalid character {ch!r} in generator {i}: {g!r}"
                    )
            clean.append(sign + body)

        self.n = n
        self.k = k
        self.generators = clean
        self.name = name or f"[[{n},{k}]]"
        self._logical_xs = _validate_logicals(logical_xs, k, n, "logical X")
        self._logical_zs = _validate_logicals(logical_zs, k, n, "logical Z")
        self._distance: Optional[int] = None

        self._validate_generators()
        self._validate_provided_logicals()

    def _validate_generators(self) -> None:
        """Assert all generators are independent and mutually commuting."""
        parsed = [_parse_pauli(g) for g in self.generators]
        mat = [x_row + z_row for _, x_row, z_row in parsed]
        expected_rank = self.n - self.k
        actual_rank = rank_gf2(mat)
        if actual_rank != expected_rank:
            raise ValueError(
                f"Generators must have rank {expected_rank}, got {actual_rank}"
            )

        for i in range(len(parsed)):
            for j in range(i + 1, len(parsed)):
                _, xi, zi = parsed[i]
                _, xj, zj = parsed[j]
                if _symplectic_product(xi, zi, xj, zj) == 1:
                    raise ValueError(
                        f"Generators {i} and {j} anticommute: "
                        f"{self.generators[i]} vs {self.generators[j]}"
                    )

    def _validate_provided_logicals(self) -> None:
        if self._logical_xs is None or self._logical_zs is None:
            return

        generator_vectors = [_pauli_to_vector(g) for g in self.generators]
        for label, operators in (
            ("logical X", self._logical_xs),
            ("logical Z", self._logical_zs),
        ):
            for i, operator in enumerate(operators):
                vec = _pauli_to_vector(operator)
                if any(_symplectic_product_vec(vec, gen) for gen in generator_vectors):
                    raise ValueError(f"{label} operator {i} does not commute with generators")
                if _is_in_span(vec, generator_vectors):
                    raise ValueError(f"{label} operator {i} is in the stabilizer group")

        for i in range(self.k):
            lx = _pauli_to_vector(self._logical_xs[i])
            lz = _pauli_to_vector(self._logical_zs[i])
            if _symplectic_product_vec(lx, lz) != 1:
                raise ValueError(f"logical X/Z pair {i} must anticommute")
            for j in range(self.k):
                if i == j:
                    continue
                other_lx = _pauli_to_vector(self._logical_xs[j])
                other_lz = _pauli_to_vector(self._logical_zs[j])
                if _symplectic_product_vec(lx, other_lx):
                    raise ValueError("logical X operators must commute")
                if _symplectic_product_vec(lz, other_lz):
                    raise ValueError("logical Z operators must commute")
                if _symplectic_product_vec(lx, other_lz):
                    raise ValueError("logical X_i must commute with logical Z_j for i != j")

    def zero_state(self) -> StabilizerState:
        """
        Return the all-zero logical codeword as a StabilizerState.

        The returned state is stabilized by all generators plus +Z_L for each
        logical qubit.
        """
        full_stabilizers = self.generators + [self.logical_z(i) for i in range(self.k)]
        return StabilizerState.from_stabilizer_list(full_stabilizers)

    @classmethod
    def zero_logical(cls, code: "StabilizerCode") -> StabilizerState:
        """Compatibility constructor for ``StabilizerCode.zero_logical(SteaneCode)``."""
        return code.zero_state()

    def encode(self, state: StabilizerState) -> None:
        """
        Encode a physical |0...0> state into the logical |0_L> codeword.

        This implementation injects the target stabilizers directly into the
        tableau. Use ``encoding_circuit()`` when an explicit circuit object is
        needed.
        """
        if state.n != self.n:
            raise ValueError(f"state has {state.n} qubits, expected {self.n}")
        target = self.zero_state()
        state.x_mat = [row[:] for row in target.x_mat]
        state.z_mat = [row[:] for row in target.z_mat]
        state.r_phase = target.r_phase[:]
        state.n = target.n

    def encoding_circuit(self):
        """
        Return a simple Clifford Circuit that approximates a CSS-style encoder.

        The authoritative zero-state preparation is ``zero_state()``. This
        circuit is a best-effort helper for simple CSS/repetition codes.
        """
        from .circuit import Circuit

        c = Circuit(self.n)
        parsed = [_parse_pauli(g) for g in self.generators]

        x_support_qubits = set()
        z_only_qubits = set()
        for _, x_row, z_row in parsed:
            for q in range(self.n):
                if x_row[q] == 1:
                    x_support_qubits.add(q)
                if z_row[q] == 1 and x_row[q] == 0:
                    z_only_qubits.add(q)

        h_qubits = x_support_qubits - z_only_qubits
        for q in sorted(h_qubits):
            c.h(q)

        for _, x_row, _ in parsed:
            pivot = -1
            for q in range(self.n):
                if x_row[q] == 1 and q in h_qubits:
                    pivot = q
                    break
            if pivot == -1:
                continue
            for q in range(self.n):
                if x_row[q] == 1 and q != pivot:
                    c.cnot(pivot, q)

        return c

    def read_syndrome(self, state: StabilizerState) -> List[int]:
        """
        Extract the full syndrome from a (possibly corrupted) codeword.
        """
        if state.n != self.n:
            raise ValueError(f"state has {state.n} qubits, expected {self.n}")
        check_ops = [_strip_sign(g) for g in self.generators]
        return _read_syndrome(state, check_ops)

    def syndrome_extractor(self, state: StabilizerState) -> SyndromeExtractor:
        """
        Return a SyndromeExtractor bound to this code and state.
        """
        if state.n != self.n:
            raise ValueError(f"state has {state.n} qubits, expected {self.n}")
        check_ops = [_strip_sign(g) for g in self.generators]
        return SyndromeExtractor(state, check_ops)

    def logical_x(self, logical_qubit: int = 0) -> str:
        """Return the logical X operator for the given logical qubit index."""
        if not (0 <= logical_qubit < self.k):
            raise IndexError(
                f"logical_qubit={logical_qubit} out of range for k={self.k}"
            )
        if self._logical_xs is None:
            self._logical_xs, self._logical_zs = self._compute_logical_operators()
        return self._logical_xs[logical_qubit]

    def logical_z(self, logical_qubit: int = 0) -> str:
        """Return the logical Z operator for the given logical qubit index."""
        if not (0 <= logical_qubit < self.k):
            raise IndexError(
                f"logical_qubit={logical_qubit} out of range for k={self.k}"
            )
        if self._logical_zs is None:
            self._logical_xs, self._logical_zs = self._compute_logical_operators()
        return self._logical_zs[logical_qubit]

    def _compute_logical_operators(self) -> Tuple[List[str], List[str]]:
        """
        Compute logical X and Z operators via the symplectic complement.
        """
        n = self.n
        stabilizer_vectors = [_pauli_to_vector(g) for g in self.generators]

        # A Pauli v = [x|z] commutes with h = [hx|hz] iff [hz|hx] . v = 0.
        constraint_matrix: List[List[int]] = []
        for h in stabilizer_vectors:
            hx = h[:n]
            hz = h[n:]
            constraint_matrix.append(hz + hx)

        normalizer_basis = _nullspace_gf2(constraint_matrix, 2 * n)
        quotient_basis: List[List[int]] = []
        span = [row[:] for row in stabilizer_vectors]
        for candidate in normalizer_basis:
            if rank_gf2(span + quotient_basis + [candidate]) > rank_gf2(
                span + quotient_basis
            ):
                quotient_basis.append(candidate)
            if len(quotient_basis) == 2 * self.k:
                break

        if len(quotient_basis) != 2 * self.k:
            raise ValueError("Could not find enough logical operators")

        remaining = [row[:] for row in quotient_basis]
        logical_xs: List[List[int]] = []
        logical_zs: List[List[int]] = []

        while remaining and len(logical_xs) < self.k:
            pair = None
            for i in range(len(remaining)):
                for j in range(i + 1, len(remaining)):
                    if _symplectic_product_vec(remaining[i], remaining[j]) == 1:
                        pair = (i, j)
                        break
                if pair is not None:
                    break
            if pair is None:
                raise ValueError("Logical basis is degenerate")

            i, j = pair
            lx = remaining[i][:]
            lz = remaining[j][:]
            logical_xs.append(lx)
            logical_zs.append(lz)

            new_remaining: List[List[int]] = []
            for index, vec in enumerate(remaining):
                if index in pair:
                    continue
                fixed = vec[:]
                if _symplectic_product_vec(fixed, lz):
                    _xor_into(fixed, lx)
                if _symplectic_product_vec(fixed, lx):
                    _xor_into(fixed, lz)
                new_remaining.append(fixed)
            remaining = new_remaining

        return (
            [_vector_to_pauli(vec) for vec in logical_xs],
            [_vector_to_pauli(vec) for vec in logical_zs],
        )

    def distance(self) -> int:
        """
        Compute the code distance d by minimum-weight normalizer search.
        """
        if self._distance is not None:
            return self._distance

        stabilizer_vectors = [_pauli_to_vector(g) for g in self.generators]
        for weight in range(1, self.n + 1):
            for positions in itertools.combinations(range(self.n), weight):
                for paulis in itertools.product(("X", "Y", "Z"), repeat=weight):
                    vec = [0] * (2 * self.n)
                    for q, pauli in zip(positions, paulis):
                        if pauli in ("X", "Y"):
                            vec[q] = 1
                        if pauli in ("Y", "Z"):
                            vec[self.n + q] = 1
                    if any(_symplectic_product_vec(vec, gen) for gen in stabilizer_vectors):
                        continue
                    if not _is_in_span(vec, stabilizer_vectors):
                        self._distance = weight
                        return weight

        raise ValueError("No non-trivial logical operator found")

    def __repr__(self) -> str:
        return f"StabilizerCode(name={self.name!r}, n={self.n}, k={self.k})"

    def __str__(self) -> str:
        lines = [f"{self.name}  [[{self.n}, {self.k}]]"]
        lines.append(f"  Generators ({len(self.generators)}):")
        for g in self.generators:
            lines.append(f"    {g}")
        return "\n".join(lines)


# --- Named code instances ---

BitFlip3Code = StabilizerCode(
    n=3,
    k=1,
    generators=["+ZZI", "+IZZ"],
    name="Bit-flip [[3,1,1]]",
    logical_xs=["+XXX"],
    logical_zs=["+IIZ"],
)
"""3-qubit bit-flip repetition code. Corrects single X errors."""

PhaseFlip3Code = StabilizerCode(
    n=3,
    k=1,
    generators=["+XXI", "+IXX"],
    name="Phase-flip [[3,1,1]]",
    logical_xs=["+IIX"],
    logical_zs=["+ZZZ"],
)
"""3-qubit phase-flip repetition code. Corrects single Z errors."""

Shor9Code = StabilizerCode(
    n=9,
    k=1,
    generators=[
        "+ZZIIIIIII",
        "+ZIZIIIIII",
        "+IIIZZIIII",
        "+IIIZIZIII",
        "+IIIIIIZZI",
        "+IIIIIIZIZ",
        "+XXXXXXIII",
        "+XXXIIIXXX",
    ],
    name="Shor [[9,1,3]]",
    logical_xs=["+XXXXXXXXX"],
    logical_zs=["+ZIIZIIZII"],
)
"""Shor 9-qubit code. Corrects arbitrary single-qubit errors."""

PerfectCode = StabilizerCode(
    n=5,
    k=1,
    generators=[
        "+XZZXI",
        "+IXZZX",
        "+XIXZZ",
        "+ZXIXZ",
    ],
    name="Perfect [[5,1,3]]",
    logical_xs=["+XXXXX"],
    logical_zs=["+ZZZZZ"],
)
"""5-qubit perfect code. Minimum code to correct any single-qubit error."""

SteaneCode = StabilizerCode(
    n=7,
    k=1,
    generators=[
        "+IIIXXXX",
        "+IXXIIXX",
        "+XIXIXIX",
        "+IIIZZZZ",
        "+IZZIIZZ",
        "+ZIZIZIZ",
    ],
    name="Steane [[7,1,3]]",
    logical_xs=["+XXXXXXX"],
    logical_zs=["+ZZZZZZZ"],
)
"""Steane 7-qubit code. CSS code based on the [7,4,3] Hamming code."""


def _build_surface_code_3() -> List[str]:
    """
    Build a distance-3, 9-data-qubit CSS surface-code-style stabilizer set.

    The row-major 3x3 layout is:

        0 1 2
        3 4 5
        6 7 8

    The checks below are independent and mutually commuting. They use the same
    9-data-qubit, 8-check [[9,1,3]] stabilizer structure used by small planar
    surface-code examples.
    """
    return [
        "+ZZIIIIIII",
        "+IZZIIIIII",
        "+IIIZZIIII",
        "+IIIIZZIII",
        "+IIIIIIZZI",
        "+IIIIIIIZZ",
        "+XXXXXXIII",
        "+IIIXXXXXX",
    ]


SurfaceCode3 = StabilizerCode(
    n=9,
    k=1,
    generators=_build_surface_code_3(),
    name="Rotated Surface [[9,1,3]]",
    logical_xs=["+XXXIIIIII"],
    logical_zs=["+ZIIZIIZII"],
)
"""Rotated distance-3 surface code [[9,1,3]]."""
