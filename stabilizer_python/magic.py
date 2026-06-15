"""
Magic state characterisation for non-Clifford quantum states.

Provides:
  - stabilizer_fidelity(decomp): candidate-term stabilizer fidelity
  - stabilizer_extent(decomp): xi = (sum_i |alpha_i|)^2
  - stabilizer_entropy(decomp): M_2 Renyi entropy over decomposition weights
  - NoisyStabilizerState: classical mixture of weighted stabilizer states
  - PauliChannel: named Pauli noise models

References:
  Bravyi, Browne, Calpin, Campbell, Gosset, Howard,
  "Simulation of quantum circuits by low-rank stabilizer decompositions",
  Quantum 3, 181 (2019). arXiv:1808.00128

  Leone, Oliviero, Hamma,
  "Stabilizer Renyi Entropy",
  PRL 128, 050402 (2022). arXiv:2106.12587
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List

from .tableau import StabilizerState

try:
    from .decomposition import _project_z_with_norm, _stab_inner_product
except ImportError as exc:  # pragma: no cover - only relevant without D1.
    raise ImportError("decomposition.py not found - run the D1 prompt first") from exc


def stabilizer_extent(decomp) -> float:
    """
    Compute the stabilizer extent xi(psi) = (sum_i |alpha_i|)^2.

    The value is 1 for a single stabilizer term and grows as the decomposition
    spreads across more weighted stabilizer states.
    """
    total = sum(abs(coeff) for coeff, _ in decomp.terms)
    return total**2


def stabilizer_entropy(decomp) -> float:
    """
    Compute the stabilizer Renyi entropy M_2.

    M_2 = -log2(sum_i |alpha_i|^4 / (sum_i |alpha_i|^2)^2)
    """
    sum_sq = sum(abs(coeff) ** 2 for coeff, _ in decomp.terms)
    sum_fourth = sum(abs(coeff) ** 4 for coeff, _ in decomp.terms)
    if sum_sq < 1e-12:
        raise ValueError("Decomposition has zero norm.")
    ratio = sum_fourth / (sum_sq**2)
    if ratio <= 0.0:
        return float("inf")
    return -math.log2(ratio)


def stabilizer_fidelity(decomp) -> float:
    """
    Compute a candidate-term stabilizer fidelity.

    The exact max over all stabilizer states can be larger than the best term
    in a chosen decomposition. This function evaluates |<S_j|psi>|^2 for each
    stabilizer state already present in the decomposition and returns the best
    candidate value.
    """
    if not decomp.terms:
        raise ValueError("Decomposition has no terms.")

    try:
        best = 0.0
        for _, state_j in decomp.terms:
            amplitude = 0.0 + 0j
            for coeff_i, state_i in decomp.terms:
                amplitude += coeff_i * _stab_inner_product(state_j, state_i)
            best = max(best, abs(amplitude) ** 2)
        return min(1.0, max(0.0, best))
    except ImportError:
        return max(abs(coeff) ** 2 for coeff, _ in decomp.terms)


@dataclass
class WeightedState:
    """A stabilizer state with a classical probability weight."""

    probability: float
    state: StabilizerState


def _pauli_string_from_generator(
    phase: int, x_row: List[int], z_row: List[int]
) -> str:
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


def _stabilizer_strings(state: StabilizerState) -> List[str]:
    if hasattr(state, "stabilizer_strings"):
        return state.stabilizer_strings()
    return [
        _pauli_string_from_generator(phase, x_row, z_row)
        for phase, x_row, z_row in state.stabilizer_generators()
    ]


class NoisyStabilizerState:
    """
    Mixed stabilizer state represented as a classical probability ensemble.

    rho = sum_i p_i |S_i><S_i|

    This is an incoherent classical mixture, not a quantum superposition. Use
    StabilizerDecomposition for coherent sums of stabilizer states.
    """

    def __init__(self, n: int):
        if n <= 0:
            raise ValueError("n must be >= 1")
        self.n = n
        self.ensemble: List[WeightedState] = [
            WeightedState(probability=1.0, state=StabilizerState.zero(n))
        ]

    @classmethod
    def from_pure(cls, state: StabilizerState) -> "NoisyStabilizerState":
        noisy = cls.__new__(cls)
        noisy.n = state.n
        noisy.ensemble = [WeightedState(probability=1.0, state=state.copy())]
        return noisy

    @property
    def ensemble_size(self) -> int:
        return len(self.ensemble)

    def _check_probability(self, probability: float, name: str) -> None:
        if probability < 0.0:
            raise ValueError(f"{name} must be >= 0")

    def _apply_clifford(self, method: str, *args: int) -> None:
        for weighted in self.ensemble:
            getattr(weighted.state, method)(*args)

    def h(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("h", q)
        return self

    def s(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("s", q)
        return self

    def sdg(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("sdg", q)
        return self

    def x(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("x", q)
        return self

    def y(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("y", q)
        return self

    def z(self, q: int) -> "NoisyStabilizerState":
        self._apply_clifford("z", q)
        return self

    def cnot(self, control: int, target: int) -> "NoisyStabilizerState":
        self._apply_clifford("cnot", control, target)
        return self

    def cx(self, control: int, target: int) -> "NoisyStabilizerState":
        return self.cnot(control, target)

    def cz(self, control: int, target: int) -> "NoisyStabilizerState":
        self._apply_clifford("cz", control, target)
        return self

    def cy(self, control: int, target: int) -> "NoisyStabilizerState":
        self._apply_clifford("cy", control, target)
        return self

    def swap(self, q1: int, q2: int) -> "NoisyStabilizerState":
        self._apply_clifford("swap", q1, q2)
        return self

    def apply_pauli_channel(
        self, q: int, p_x: float, p_y: float, p_z: float
    ) -> "NoisyStabilizerState":
        for name, probability in (("p_x", p_x), ("p_y", p_y), ("p_z", p_z)):
            self._check_probability(probability, name)
        p_i = 1.0 - p_x - p_y - p_z
        if p_i < -1e-12:
            raise ValueError(
                f"Error probabilities sum to {p_x + p_y + p_z:.4f} > 1"
            )
        p_i = max(0.0, p_i)

        new_ensemble: List[WeightedState] = []
        for weighted in self.ensemble:
            probability, state = weighted.probability, weighted.state
            if p_i > 0.0:
                new_ensemble.append(WeightedState(probability * p_i, state.copy()))
            if p_x > 0.0:
                branch = state.copy()
                branch.x(q)
                new_ensemble.append(WeightedState(probability * p_x, branch))
            if p_y > 0.0:
                branch = state.copy()
                branch.y(q)
                new_ensemble.append(WeightedState(probability * p_y, branch))
            if p_z > 0.0:
                branch = state.copy()
                branch.z(q)
                new_ensemble.append(WeightedState(probability * p_z, branch))

        self.ensemble = new_ensemble
        self._renormalise()
        return self

    def apply_depolarising(self, q: int, p: float) -> "NoisyStabilizerState":
        self._check_probability(p, "p")
        return self.apply_pauli_channel(q, p / 3.0, p / 3.0, p / 3.0)

    def apply_bit_flip(self, q: int, p: float) -> "NoisyStabilizerState":
        self._check_probability(p, "p")
        return self.apply_pauli_channel(q, p, 0.0, 0.0)

    def apply_phase_flip(self, q: int, p: float) -> "NoisyStabilizerState":
        self._check_probability(p, "p")
        return self.apply_pauli_channel(q, 0.0, 0.0, p)

    def measure_z(self, q: int) -> int:
        branches = {0: [], 1: []}
        probabilities = {0: 0.0, 1: 0.0}

        for weighted in self.ensemble:
            for outcome in (0, 1):
                projected = _project_z_with_norm(weighted.state, q, outcome)
                if projected is None:
                    continue
                projected_state, norm = projected
                branch_probability = weighted.probability * (norm**2)
                branches[outcome].append(
                    WeightedState(branch_probability, projected_state)
                )
                probabilities[outcome] += branch_probability

        total = probabilities[0] + probabilities[1]
        if total <= 1e-12:
            raise ValueError("Ensemble has collapsed to zero probability.")

        p0 = probabilities[0] / total
        chosen = 0 if random.random() < p0 else 1
        self.ensemble = branches[chosen]
        self._renormalise()
        return chosen

    def _renormalise(self) -> None:
        total = sum(weighted.probability for weighted in self.ensemble)
        if total < 1e-12:
            raise ValueError("Ensemble has collapsed to zero probability.")
        for weighted in self.ensemble:
            weighted.probability /= total

    def prune(self, threshold: float = 1e-10) -> "NoisyStabilizerState":
        self.ensemble = [
            weighted
            for weighted in self.ensemble
            if weighted.probability > threshold
        ]
        self._renormalise()
        return self

    def dominant_state(self) -> StabilizerState:
        best = max(self.ensemble, key=lambda weighted: weighted.probability)
        return best.state.copy()

    def dominant_probability(self) -> float:
        return max(weighted.probability for weighted in self.ensemble)

    def summary(self) -> str:
        lines = [
            f"NoisyStabilizerState: n={self.n}, "
            f"ensemble_size={self.ensemble_size}",
            "",
        ]
        for index, weighted in enumerate(
            sorted(self.ensemble, key=lambda item: -item.probability)
        ):
            lines.append(f"  [{index}] p={weighted.probability:.6f}")
            for generator in _stabilizer_strings(weighted.state):
                lines.append(f"       {generator}")
            lines.append("")
        return "\n".join(lines)


@dataclass
class PauliChannel:
    """A named Pauli noise channel parameterised by error probabilities."""

    p_x: float
    p_y: float
    p_z: float
    name: str = "custom"

    @classmethod
    def depolarising(cls, p: float) -> "PauliChannel":
        return cls(p_x=p / 3.0, p_y=p / 3.0, p_z=p / 3.0, name=f"depolarising(p={p})")

    @classmethod
    def bit_flip(cls, p: float) -> "PauliChannel":
        return cls(p_x=p, p_y=0.0, p_z=0.0, name=f"bit_flip(p={p})")

    @classmethod
    def phase_flip(cls, p: float) -> "PauliChannel":
        return cls(p_x=0.0, p_y=0.0, p_z=p, name=f"phase_flip(p={p})")

    @classmethod
    def bit_phase_flip(cls, p: float) -> "PauliChannel":
        return cls(p_x=0.0, p_y=p, p_z=0.0, name=f"bit_phase_flip(p={p})")

    def apply(self, state: NoisyStabilizerState, qubit: int) -> NoisyStabilizerState:
        return state.apply_pauli_channel(qubit, self.p_x, self.p_y, self.p_z)

    def apply_all(self, state: NoisyStabilizerState) -> NoisyStabilizerState:
        for q in range(state.n):
            self.apply(state, q)
        return state

