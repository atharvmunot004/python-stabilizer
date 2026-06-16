"""
Single-shot Pauli noise channels for Monte Carlo QEC decoder benchmarking.

These functions apply *one sampled Pauli error* per call to a StabilizerState
and return which error was applied. This is the correct model for shot-based
Monte Carlo simulation:

    for _ in range(n_shots):
        state = encode_logical_zero()
        errors = apply_noise(state, p)   # one random error per qubit
        syndrome = read_syndrome(state)
        correction = decoder(syndrome)
        logical_error = check_logical(state, correction)

Contrast with NoisyStabilizerState (in magic.py), which tracks all error
branches simultaneously as a weighted ensemble. That is exact mixed-state
simulation; this is faster single-trajectory simulation for threshold plots.
"""
from __future__ import annotations

import random
from typing import Callable, Dict, List, Optional, Tuple, Union

from .circuit import Circuit
from .tableau import StabilizerState


def apply_pauli_channel(
    state: StabilizerState,
    qubit: int,
    p_x: float,
    p_y: float,
    p_z: float,
) -> str:
    """
    Apply a single random Pauli error to one qubit and return which error occurred.
    """
    if p_x < 0 or p_y < 0 or p_z < 0:
        raise ValueError(
            f"Error probabilities must be non-negative, got "
            f"p_x={p_x}, p_y={p_y}, p_z={p_z}"
        )
    p_total = p_x + p_y + p_z
    if p_total > 1.0 + 1e-12:
        raise ValueError(f"Error probabilities sum to {p_total:.6f} > 1")
    state._check_qubit(qubit)

    r = random.random()
    if r < p_x:
        state.x(qubit)
        return "X"
    if r < p_x + p_y:
        state.y(qubit)
        return "Y"
    if r < p_total:
        state.z(qubit)
        return "Z"
    return "I"


def apply_depolarizing(state: StabilizerState, qubit: int, p: float) -> str:
    """
    Apply depolarizing noise to one qubit.
    """
    if p < 0 or p > 1.0 + 1e-12:
        raise ValueError(f"Depolarizing probability must be in [0, 1], got {p}")
    return apply_pauli_channel(state, qubit, p / 3.0, p / 3.0, p / 3.0)


def apply_bit_flip(state: StabilizerState, qubit: int, p: float) -> str:
    """
    Apply a bit-flip (X) error with probability p.
    """
    if p < 0 or p > 1.0 + 1e-12:
        raise ValueError(f"Bit-flip probability must be in [0, 1], got {p}")
    return apply_pauli_channel(state, qubit, p, 0.0, 0.0)


def apply_phase_flip(state: StabilizerState, qubit: int, p: float) -> str:
    """
    Apply a phase-flip (Z) error with probability p.
    """
    if p < 0 or p > 1.0 + 1e-12:
        raise ValueError(f"Phase-flip probability must be in [0, 1], got {p}")
    return apply_pauli_channel(state, qubit, 0.0, 0.0, p)


def apply_bit_phase_flip(state: StabilizerState, qubit: int, p: float) -> str:
    """
    Apply a combined bit-phase-flip (Y) error with probability p.
    """
    if p < 0 or p > 1.0 + 1e-12:
        raise ValueError(f"Bit-phase-flip probability must be in [0, 1], got {p}")
    return apply_pauli_channel(state, qubit, 0.0, p, 0.0)


def apply_pauli_channel_all(
    state: StabilizerState,
    p_x: float,
    p_y: float,
    p_z: float,
    qubits: Optional[List[int]] = None,
) -> List[str]:
    """
    Apply an independent Pauli channel to every qubit or a specified subset.
    """
    targets = qubits if qubits is not None else list(range(state.n))
    return [apply_pauli_channel(state, q, p_x, p_y, p_z) for q in targets]


def apply_depolarizing_all(
    state: StabilizerState,
    p: float,
    qubits: Optional[List[int]] = None,
) -> List[str]:
    """
    Apply independent depolarizing noise to every qubit or a subset.
    """
    targets = qubits if qubits is not None else list(range(state.n))
    return [apply_depolarizing(state, q, p) for q in targets]


def apply_bit_flip_all(
    state: StabilizerState,
    p: float,
    qubits: Optional[List[int]] = None,
) -> List[str]:
    """Apply independent bit-flip noise to every qubit or a subset."""
    targets = qubits if qubits is not None else list(range(state.n))
    return [apply_bit_flip(state, q, p) for q in targets]


def apply_phase_flip_all(
    state: StabilizerState,
    p: float,
    qubits: Optional[List[int]] = None,
) -> List[str]:
    """Apply independent phase-flip noise to every qubit or a subset."""
    targets = qubits if qubits is not None else list(range(state.n))
    return [apply_phase_flip(state, q, p) for q in targets]


class NoisyCircuit(Circuit):
    """
    A Circuit subclass that injects Pauli noise during run().

    After every gate, applies independent depolarizing noise with probability
    ``gate_error`` to each qubit the gate touched. Before every measurement, the
    quantum state is measured normally and the returned classical bit is flipped
    with probability ``meas_error``.
    """

    def __init__(
        self,
        n: int,
        gate_error: float = 0.0,
        meas_error: float = 0.0,
    ):
        super().__init__(n)
        if gate_error < 0 or gate_error > 1.0 + 1e-12:
            raise ValueError(f"gate_error must be in [0, 1], got {gate_error}")
        if meas_error < 0 or meas_error > 1.0 + 1e-12:
            raise ValueError(f"meas_error must be in [0, 1], got {meas_error}")
        self.gate_error = gate_error
        self.meas_error = meas_error

    def _apply_gate_noise(self, state: StabilizerState, qubits: Tuple[int, ...]) -> None:
        """Apply depolarizing noise to qubits touched by a gate."""
        if self.gate_error > 0.0:
            for q in qubits:
                apply_depolarizing(state, q, self.gate_error)

    def run(self, state: "StabilizerState | QuantumSimulator") -> List[int]:  # type: ignore[override]  # noqa: F821
        """
        Apply all operations with noise injection.
        """
        from .simulator import QuantumSimulator

        if isinstance(state, QuantumSimulator):
            return super().run(state)

        if not isinstance(state, StabilizerState):
            raise TypeError(
                f"NoisyCircuit.run expects StabilizerState or QuantumSimulator, "
                f"got {type(state).__name__}"
            )
        if state.n < self.n_qubits:
            raise ValueError("State has fewer qubits than circuit")

        out: List[int] = []
        for op in self.ops:
            if op.name.startswith("MZ"):
                real_outcome = state.measure_z(op.targets[0])
                if self.meas_error > 0.0 and random.random() < self.meas_error:
                    out.append(1 - real_outcome)
                else:
                    out.append(real_outcome)
                continue

            if op.gate_obj is not None:
                if not op.gate_obj.is_clifford:
                    raise ValueError(
                        "NoisyCircuit with StabilizerState supports only Clifford gates; "
                        "run non-Clifford circuits on QuantumSimulator."
                    )
                sim = QuantumSimulator(state.n)
                sim.tableau = state
                sim.apply_gate(op.gate_obj, list(op.targets))
            elif op.name == "H":
                state.h(op.targets[0])
            elif op.name == "S":
                state.s(op.targets[0])
            elif op.name == "X":
                state.x(op.targets[0])
            elif op.name == "Z":
                state.z(op.targets[0])
            elif op.name == "CNOT":
                state.cnot(op.targets[0], op.targets[1])
            else:
                raise ValueError(f"Unknown op in NoisyCircuit.run: {op.name}")

            self._apply_gate_noise(state, op.targets)

        return out


def run_shots(
    encode_fn: Callable[[StabilizerState], None],
    check_operators: List[str],
    decoder_fn: Callable[[List[int]], List[Tuple[int, str]]],
    noise_channel: Callable[[StabilizerState], None],
    n_shots: int,
    n_data: int,
    logical_x: Optional[str] = None,
    logical_z: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Union[float, int]]:
    """
    Run n_shots rounds of encode -> noise -> syndrome -> decode -> check.
    """
    from .syndrome import read_syndrome

    if n_shots < 0:
        raise ValueError(f"n_shots must be non-negative, got {n_shots}")
    if n_data <= 0:
        raise ValueError(f"n_data must be positive, got {n_data}")

    if seed is not None:
        random.seed(seed)

    logical_errors = 0
    x_errors = 0
    z_errors = 0

    for _ in range(n_shots):
        state = StabilizerState.zero(n_data)
        encode_fn(state)

        noise_channel(state)

        syndrome = read_syndrome(state, check_operators)
        correction = decoder_fn(syndrome)
        for qubit, pauli in correction:
            if pauli == "X":
                state.x(qubit)
            elif pauli == "Y":
                state.y(qubit)
            elif pauli == "Z":
                state.z(qubit)
            else:
                raise ValueError(f"Unknown correction Pauli {pauli!r}")

        has_logical = False

        if logical_z is not None and _pauli_anticommutes_with_state(
            state, logical_z.lstrip("+-")
        ):
            x_errors += 1
            has_logical = True

        if logical_x is not None and _pauli_anticommutes_with_state(
            state, logical_x.lstrip("+-")
        ):
            z_errors += 1
            has_logical = True

        if has_logical:
            logical_errors += 1

    return {
        "n_shots": n_shots,
        "logical_errors": logical_errors,
        "logical_error_rate": logical_errors / n_shots if n_shots > 0 else 0.0,
        "x_errors": x_errors,
        "z_errors": z_errors,
    }


def _pauli_anticommutes_with_state(
    state: StabilizerState, pauli_str: str
) -> bool:
    """
    Check whether a Pauli indicates a residual logical error.

    For logical-zero Monte Carlo checks, the robust signal is that the supplied
    logical stabilizer is present with negative sign after correction. For
    example, a residual ``XXX`` on the bit-flip code flips ``+IIZ`` to ``-IIZ``.
    A clean ``|0_L>`` state is not a logical-X eigenstate, so mere
    anticommutation with logical X is not counted as an error here.
    """
    n = state.n
    if len(pauli_str) != n:
        raise ValueError(f"Pauli string length {len(pauli_str)} != n_data={n}")

    x_op: List[int] = []
    z_op: List[int] = []
    for ch in pauli_str.upper():
        if ch == "I":
            x_op.append(0)
            z_op.append(0)
        elif ch == "X":
            x_op.append(1)
            z_op.append(0)
        elif ch == "Y":
            x_op.append(1)
            z_op.append(1)
        elif ch == "Z":
            x_op.append(0)
            z_op.append(1)
        else:
            raise ValueError(f"Invalid Pauli character {ch!r}")

    phase = _stabilizer_product_phase_for(state, x_op, z_op)
    return phase == 1


def _stabilizer_product_phase_for(
    state: StabilizerState, target_x: List[int], target_z: List[int]
) -> Optional[int]:
    """Return the phase of target if target is in the stabilizer group."""
    n = state.n
    rows = [state.x_mat[n + i][:] + state.z_mat[n + i][:] for i in range(n)]
    target = target_x + target_z
    solution = _solve_gf2_product(rows, target)
    if solution is None:
        return None

    work = state.copy()
    accumulator = 0
    work.x_mat[accumulator] = [0] * n
    work.z_mat[accumulator] = [0] * n
    work.r_phase[accumulator] = 0

    for i, include in enumerate(solution):
        if include:
            work._rowmult(accumulator, n + i)

    if work.x_mat[accumulator] == target_x and work.z_mat[accumulator] == target_z:
        return work.r_phase[accumulator]
    return None


def _solve_gf2_product(rows: List[List[int]], target: List[int]) -> Optional[List[int]]:
    """Solve XOR of selected rows == target over GF(2), returning coefficients."""
    if not rows:
        return [] if not any(target) else None

    n_rows = len(rows)
    n_cols = len(target)
    # Transpose equations so each column of the original rows is one equation.
    augmented = []
    for col in range(n_cols):
        augmented.append([rows[row][col] for row in range(n_rows)] + [target[col]])

    pivot_cols: List[int] = []
    pivot_row = 0
    for col in range(n_rows):
        found = -1
        for r in range(pivot_row, n_cols):
            if augmented[r][col] == 1:
                found = r
                break
        if found == -1:
            continue
        augmented[pivot_row], augmented[found] = augmented[found], augmented[pivot_row]
        pivot_cols.append(col)
        for r in range(n_cols):
            if r != pivot_row and augmented[r][col] == 1:
                for c in range(col, n_rows + 1):
                    augmented[r][c] ^= augmented[pivot_row][c]
        pivot_row += 1
        if pivot_row == n_cols:
            break

    for r in range(pivot_row, n_cols):
        if all(augmented[r][c] == 0 for c in range(n_rows)) and augmented[r][n_rows]:
            return None

    solution = [0] * n_rows
    for row_index, pivot_col in enumerate(pivot_cols):
        solution[pivot_col] = augmented[row_index][n_rows]
    return solution
