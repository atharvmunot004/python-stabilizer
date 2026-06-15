"""
Stabilizer rank decomposition backend.

Represents a quantum state as a weighted sum of stabilizer states:

    |psi> = sum_i alpha_i |S_i>

where each |S_i> is a StabilizerState and alpha_i is a complex coefficient.
Clifford gates are applied to each term independently. T and Tdg gates split
terms by post-selecting the Z eigenspaces of the target qubit.

Reference: Bravyi, Browne, Calpin, Campbell, Gosset, Howard,
"Simulation of quantum circuits by low-rank stabilizer decompositions",
Quantum 3, 181 (2019). arXiv:1808.00128
"""
from __future__ import annotations

import cmath
import math
import random
from typing import List, Optional, Tuple

from .linear_algebra import rank_gf2
from .tableau import StabilizerState


Term = Tuple[complex, StabilizerState]
ProjectedTerm = Tuple[StabilizerState, float]


def _is_deterministic_z(state: StabilizerState, q: int) -> Tuple[bool, int]:
    """
    Check whether measuring Z on qubit q is deterministic without modifying state.

    Returns (True, outcome) for deterministic measurements and (False, -1) when
    the measurement has both outcomes with probability 1/2.
    """
    state._check_qubit(q)
    if state.z_measurement_branch(q) == "random":
        return False, -1
    return True, state._deterministic_z_outcome(q)


def _force_random_z_branch(
    state: StabilizerState, q: int, forced_outcome: int
) -> StabilizerState:
    """
    Return the tableau obtained by post-selecting a random Z measurement branch.

    This mirrors StabilizerState.measure_z, but uses forced_outcome instead of
    sampling. The input must be a state where Z_q measurement is random.
    """
    n = state.n
    s = state.copy()

    pivot = -1
    for r in range(n, 2 * n):
        if s.x_mat[r][q] == 1:
            pivot = r
            break
    if pivot == -1:
        raise ValueError("Z measurement is deterministic; cannot force branch")

    for r in range(2 * n):
        if r != pivot and s.x_mat[r][q] == 1:
            s._rowmult(r, pivot)

    s._rowswap(pivot, n + q)

    for j in range(n):
        s.x_mat[n + q][j] = 0
        s.z_mat[n + q][j] = 0
    s.z_mat[n + q][q] = 1
    s.r_phase[n + q] = forced_outcome

    for j in range(n):
        s.x_mat[q][j] = 0
        s.z_mat[q][j] = 0
    s.x_mat[q][q] = 1
    s.r_phase[q] = 0

    return s


def _project_z_with_norm(
    state: StabilizerState, q: int, forced_outcome: int
) -> Optional[ProjectedTerm]:
    """
    Project state onto the Z eigenspace selected by forced_outcome.

    Returns (normalized_projected_state, sqrt(probability)) or None when the
    projection has zero support.
    """
    if forced_outcome not in (0, 1):
        raise ValueError("forced_outcome must be 0 or 1")

    deterministic, outcome = _is_deterministic_z(state, q)
    if deterministic:
        if outcome != forced_outcome:
            return None
        return state.copy(), 1.0

    return _force_random_z_branch(state, q, forced_outcome), 1.0 / math.sqrt(2.0)


def _project_z(
    state: StabilizerState, q: int, forced_outcome: int
) -> Optional[StabilizerState]:
    """
    Project a copy of state onto Z=+1 (0) or Z=-1 (1) on qubit q.

    Returns a normalized StabilizerState in the projected subspace, or None if
    the projection yields zero. Coefficient scaling is handled internally by
    StabilizerDecomposition via _project_z_with_norm.
    """
    projected = _project_z_with_norm(state, q, forced_outcome)
    return None if projected is None else projected[0]


def _terms_norm_squared(terms: List[Term]) -> float:
    total = 0.0 + 0j
    for coeff_i, state_i in terms:
        for coeff_j, state_j in terms:
            total += coeff_i.conjugate() * coeff_j * _stab_inner_product(
                state_i, state_j
            )
    return max(0.0, total.real)


class StabilizerDecomposition:
    """
    Simulate a quantum state as a sum of stabilizer states.

    Clifford gates are exact and applied independently to each term. Each T or
    Tdg gate can double the number of terms, so a circuit with t such gates has
    at most 2^t terms before any later simplification.
    """

    def __init__(self, n: int):
        if n <= 0:
            raise ValueError("n must be >= 1")
        self.n = n
        self.terms: List[Term] = [(1.0 + 0j, StabilizerState.zero(n))]
        self.t_count = 0

    @property
    def term_count(self) -> int:
        return len(self.terms)

    def _check_qubit(self, q: int) -> None:
        if not (0 <= q < self.n):
            raise ValueError(f"q={q} out of range for {self.n}-qubit state")

    def _apply_clifford(self, method: str, *args: int) -> None:
        for _, state in self.terms:
            getattr(state, method)(*args)

    def i(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("i", q)
        return self

    def h(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("h", q)
        return self

    def s(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("s", q)
        return self

    def sdg(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("sdg", q)
        return self

    def s_dagger(self, q: int) -> "StabilizerDecomposition":
        return self.sdg(q)

    def sx(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("sx", q)
        return self

    def sqrt_x(self, q: int) -> "StabilizerDecomposition":
        return self.sx(q)

    def sxdg(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("sxdg", q)
        return self

    def sqrt_x_dagger(self, q: int) -> "StabilizerDecomposition":
        return self.sxdg(q)

    def x(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("x", q)
        return self

    def y(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("y", q)
        return self

    def z(self, q: int) -> "StabilizerDecomposition":
        self._apply_clifford("z", q)
        return self

    def cnot(self, control: int, target: int) -> "StabilizerDecomposition":
        self._apply_clifford("cnot", control, target)
        return self

    def cx(self, control: int, target: int) -> "StabilizerDecomposition":
        return self.cnot(control, target)

    def cz(self, control: int, target: int) -> "StabilizerDecomposition":
        self._apply_clifford("cz", control, target)
        return self

    def cy(self, control: int, target: int) -> "StabilizerDecomposition":
        self._apply_clifford("cy", control, target)
        return self

    def swap(self, q1: int, q2: int) -> "StabilizerDecomposition":
        self._apply_clifford("swap", q1, q2)
        return self

    def _apply_t_like(self, q: int, phase_one_branch: complex) -> None:
        self._check_qubit(q)
        new_terms: List[Term] = []
        for coeff, state in self.terms:
            branch0 = _project_z_with_norm(state, q, 0)
            if branch0 is not None:
                state0, norm0 = branch0
                new_terms.append((coeff * norm0, state0))

            branch1 = _project_z_with_norm(state, q, 1)
            if branch1 is not None:
                state1, norm1 = branch1
                new_terms.append((coeff * norm1 * phase_one_branch, state1))

        self.terms = new_terms
        self.t_count += 1

    def t(self, q: int) -> "StabilizerDecomposition":
        """Apply T by splitting each term into Z=+1 and Z=-1 branches."""
        self._apply_t_like(q, cmath.exp(1j * math.pi / 4.0))
        return self

    def tdg(self, q: int) -> "StabilizerDecomposition":
        """Apply Tdg by splitting each term with the conjugate T phase."""
        self._apply_t_like(q, cmath.exp(-1j * math.pi / 4.0))
        return self

    def rz(self, q: int, theta: float) -> "StabilizerDecomposition":
        raise NotImplementedError(
            "StabilizerDecomposition currently supports exact T/Tdg "
            "non-Clifford splitting only; use QuantumSimulator for arbitrary Rz."
        )

    def rx(self, q: int, theta: float) -> "StabilizerDecomposition":
        raise NotImplementedError(
            "StabilizerDecomposition currently supports exact T/Tdg "
            "non-Clifford splitting only; use QuantumSimulator for arbitrary Rx."
        )

    def ry(self, q: int, theta: float) -> "StabilizerDecomposition":
        raise NotImplementedError(
            "StabilizerDecomposition currently supports exact T/Tdg "
            "non-Clifford splitting only; use QuantumSimulator for arbitrary Ry."
        )

    def expectation_z(self, q: int) -> float:
        """Compute <psi|Z_q|psi> for terms where Z_q acts diagonally."""
        self._check_qubit(q)
        total = 0.0 + 0j
        for coeff_i, state_i in self.terms:
            z_exp = _stabilizer_z_expectation(state_i, q)
            if z_exp == 0:
                continue
            for coeff_j, state_j in self.terms:
                total += (
                    coeff_j.conjugate()
                    * coeff_i
                    * z_exp
                    * _stab_inner_product(state_j, state_i)
                )
        return total.real

    def inner_product_with_zero(self) -> complex:
        zero = StabilizerState.zero(self.n)
        total = 0.0 + 0j
        for coeff, state in self.terms:
            total += coeff * _stab_inner_product(zero, state)
        return total

    def measure_z(self, q: int) -> int:
        """Sample and collapse a Z measurement using projected decompositions."""
        self._check_qubit(q)
        branches = {}
        probabilities = {}
        for outcome in (0, 1):
            projected_terms: List[Term] = []
            for coeff, state in self.terms:
                projected = _project_z_with_norm(state, q, outcome)
                if projected is not None:
                    projected_state, norm = projected
                    projected_terms.append((coeff * norm, projected_state))
            branches[outcome] = projected_terms
            probabilities[outcome] = _terms_norm_squared(projected_terms)

        total_probability = probabilities[0] + probabilities[1]
        if total_probability <= 1e-12:
            raise RuntimeError("measurement probabilities vanished")

        p0 = probabilities[0] / total_probability
        outcome = 0 if random.random() < p0 else 1

        norm = math.sqrt(probabilities[outcome])
        if norm <= 1e-12:
            self.terms = []
        else:
            self.terms = [(coeff / norm, state) for coeff, state in branches[outcome]]
        return outcome

    def summary(self) -> str:
        lines = [
            f"StabilizerDecomposition: n={self.n}, "
            f"terms={self.term_count}, t_gates_applied={self.t_count}",
            "",
        ]
        for i, (coeff, state) in enumerate(self.terms):
            mag = abs(coeff)
            angle_deg = math.degrees(cmath.phase(coeff))
            lines.append(
                f"  Term {i}: coeff={coeff:.4f}  "
                f"(|alpha|={mag:.4f}, arg={angle_deg:.1f} deg)"
            )
            for generator in state.stabilizer_strings():
                lines.append(f"    {generator}")
            lines.append("")
        return "\n".join(lines)


def _pauli_anticommutes(
    left_x: List[int], left_z: List[int], right_x: List[int], right_z: List[int]
) -> bool:
    total = 0
    for lx, lz, rx, rz in zip(left_x, left_z, right_x, right_z):
        total ^= lx & rz
        total ^= lz & rx
    return total == 1


def _stab_inner_product(bra: StabilizerState, ket: StabilizerState) -> complex:
    """
    Compute a conservative stabilizer-state overlap estimate.

    This is exact for identical tableaus and for states with contradictory
    stabilizer generators. For remaining non-orthogonal cases it returns the
    standard stabilizer-overlap magnitude derived from the rank of the combined
    unsigned generator matrix and omits the global phase.
    """
    if bra.n != ket.n:
        raise ValueError("States must have the same number of qubits")
    if (
        bra.x_mat == ket.x_mat
        and bra.z_mat == ket.z_mat
        and bra.r_phase == ket.r_phase
    ):
        return 1.0 + 0j

    n = bra.n
    for phase_a, x_a, z_a in bra.stabilizer_generators():
        for phase_b, x_b, z_b in ket.stabilizer_generators():
            if x_a == x_b and z_a == z_b and phase_a != phase_b:
                return 0.0 + 0j

    combined = []
    for _, x_row, z_row in bra.stabilizer_generators():
        combined.append(x_row + z_row)
    for _, x_row, z_row in ket.stabilizer_generators():
        combined.append(x_row + z_row)

    rank = rank_gf2(combined)
    magnitude = 2.0 ** (-(rank - n) / 2.0)

    # Anticommuting generator descriptions can still describe non-orthogonal
    # states (for example |0> and |+>), so they affect the magnitude through
    # rank rather than forcing zero.
    return magnitude + 0j


def _stabilizer_z_expectation(state: StabilizerState, q: int) -> int:
    deterministic, outcome = _is_deterministic_z(state, q)
    if not deterministic:
        return 0
    return -1 if outcome else 1

