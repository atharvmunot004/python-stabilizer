"""
Shot-based syndrome sampling for QEC decoder benchmarking.

Provides a high-level API integrated with StabilizerCode and EncodedState for
threshold plots and decoder evaluation.
"""
from __future__ import annotations

import itertools
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .tableau import StabilizerState


@dataclass
class ShotRecord:
    """Per-shot record for detailed analysis."""

    shot_index: int
    syndrome: List[int]
    correction: List[Tuple[int, str]]
    logical_error_type: str
    had_logical_error: bool


@dataclass
class CodeBenchmarkResult:
    """Aggregated result from a single benchmark_code() call."""

    n_shots: int
    n_logical_errors: int
    logical_error_rate: float
    n_x_errors: int
    n_z_errors: int
    x_error_rate: float
    z_error_rate: float
    elapsed_seconds: float
    shots_per_second: float
    seed: Optional[int]
    records: List[ShotRecord] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "CodeBenchmarkResult:",
            f"  shots          = {self.n_shots}",
            f"  logical errors = {self.n_logical_errors}",
            f"  logical rate   = {self.logical_error_rate:.4f}",
            f"  X error rate   = {self.x_error_rate:.4f}",
            f"  Z error rate   = {self.z_error_rate:.4f}",
            f"  time           = {self.elapsed_seconds:.2f}s",
            f"  throughput     = {self.shots_per_second:.1f} shots/s",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            "CodeBenchmarkResult("
            f"n_shots={self.n_shots}, "
            f"logical_error_rate={self.logical_error_rate:.4f})"
        )


@dataclass
class ThresholdScanResult:
    """Result from a threshold_scan() call."""

    p_values: List[float]
    logical_error_rates: List[float]
    x_error_rates: List[float]
    z_error_rates: List[float]
    n_shots_per_p: int
    code_name: str
    benchmark_results: List[CodeBenchmarkResult]

    def as_dict(self) -> Dict[float, float]:
        """Return {p: logical_error_rate} for quick plotting."""
        return dict(zip(self.p_values, self.logical_error_rates))

    def summary(self) -> str:
        lines = [
            f"ThresholdScanResult: {self.code_name}",
            f"  n_shots_per_p = {self.n_shots_per_p}",
            f"  {'p':>8}  {'p_L':>8}  {'p_X':>8}  {'p_Z':>8}",
            f"  {'-' * 38}",
        ]
        for p, p_l, p_x, p_z in zip(
            self.p_values,
            self.logical_error_rates,
            self.x_error_rates,
            self.z_error_rates,
        ):
            lines.append(f"  {p:>8.4f}  {p_l:>8.4f}  {p_x:>8.4f}  {p_z:>8.4f}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            "ThresholdScanResult("
            f"code={self.code_name!r}, "
            f"p_values={self.p_values}, "
            f"rates={[round(r, 4) for r in self.logical_error_rates]})"
        )


def benchmark_code(
    code,
    noise_model: Callable[[StabilizerState], None],
    decoder: Callable[[List[int]], List[Tuple[int, str]]],
    n_shots: int,
    *,
    seed: Optional[int] = None,
    record_shots: bool = False,
    verbose: bool = False,
) -> CodeBenchmarkResult:
    """
    Run n_shots rounds of encode -> noise -> syndrome -> decode -> check.
    """
    from .encoded_state import EncodedState

    if n_shots < 0:
        raise ValueError(f"n_shots must be non-negative, got {n_shots}")
    if seed is not None:
        random.seed(seed)

    n_logical_errors = 0
    n_x_errors = 0
    n_z_errors = 0
    records: List[ShotRecord] = []
    verbose_interval = max(1, n_shots // 10)

    t_start = time.perf_counter()

    for shot_idx in range(n_shots):
        state = StabilizerState.zero(code.n)
        code.encode(state)

        noise_model(state)

        syndrome = code.read_syndrome(state)
        correction = decoder(syndrome)

        for qubit, pauli in correction:
            if pauli == "X":
                state.x(qubit)
            elif pauli == "Y":
                state.y(qubit)
            elif pauli == "Z":
                state.z(qubit)
            else:
                raise ValueError(f"Unknown correction Pauli {pauli!r}")

        enc = EncodedState(state, code)
        # benchmark_code always starts from logical |0_L>; the wrapper is
        # constructed post-correction, so reset its frame to the intended input.
        enc._expected_z = [+1 for _ in range(enc.k)]
        enc._expected_x = [None for _ in range(enc.k)]

        had_x_err = any(enc.has_logical_x_error(i) for i in range(enc.k))
        had_z_err = any(enc.has_logical_z_error(i) for i in range(enc.k))
        had_error = had_x_err or had_z_err

        if had_x_err:
            n_x_errors += 1
        if had_z_err:
            n_z_errors += 1
        if had_error:
            n_logical_errors += 1

        if record_shots:
            error_type = _combined_error_type(had_x_err, had_z_err)
            records.append(
                ShotRecord(
                    shot_index=shot_idx,
                    syndrome=list(syndrome),
                    correction=list(correction),
                    logical_error_type=error_type,
                    had_logical_error=had_error,
                )
            )

        if verbose and (shot_idx + 1) % verbose_interval == 0:
            pct = 100 * (shot_idx + 1) // n_shots if n_shots else 100
            current_rate = n_logical_errors / (shot_idx + 1)
            print(
                f"  [{pct:3d}%] shot {shot_idx + 1}/{n_shots} "
                f"| logical errors: {n_logical_errors} "
                f"| rate: {current_rate:.4f}"
            )

    elapsed = time.perf_counter() - t_start
    return CodeBenchmarkResult(
        n_shots=n_shots,
        n_logical_errors=n_logical_errors,
        logical_error_rate=n_logical_errors / n_shots if n_shots > 0 else 0.0,
        n_x_errors=n_x_errors,
        n_z_errors=n_z_errors,
        x_error_rate=n_x_errors / n_shots if n_shots > 0 else 0.0,
        z_error_rate=n_z_errors / n_shots if n_shots > 0 else 0.0,
        elapsed_seconds=elapsed,
        shots_per_second=n_shots / elapsed if elapsed > 0 else 0.0,
        seed=seed,
        records=records,
    )


def threshold_scan(
    code,
    noise_model_factory: Callable[[float], Callable[[StabilizerState], None]],
    decoder: Callable[[List[int]], List[Tuple[int, str]]],
    p_values: List[float],
    n_shots_per_p: int,
    *,
    seed: Optional[int] = None,
    verbose: bool = True,
) -> ThresholdScanResult:
    """
    Sweep physical error rate p across p_values and return logical error rates.
    """
    if verbose:
        print(
            f"threshold_scan: {code.name}, "
            f"{len(p_values)} p-values, "
            f"{n_shots_per_p} shots each"
        )

    benchmark_results: List[CodeBenchmarkResult] = []
    logical_rates: List[float] = []
    x_rates: List[float] = []
    z_rates: List[float] = []

    for i, p in enumerate(p_values):
        p_seed = None if seed is None else seed + 10 * i
        noise_model = noise_model_factory(p)

        if verbose:
            print(f"  p={p:.4f} ...", end=" ", flush=True)

        result = benchmark_code(
            code,
            noise_model=noise_model,
            decoder=decoder,
            n_shots=n_shots_per_p,
            seed=p_seed,
            verbose=False,
        )

        benchmark_results.append(result)
        logical_rates.append(result.logical_error_rate)
        x_rates.append(result.x_error_rate)
        z_rates.append(result.z_error_rate)

        if verbose:
            print(
                f"p_L={result.logical_error_rate:.4f}  "
                f"({result.shots_per_second:.0f} shots/s)"
            )

    return ThresholdScanResult(
        p_values=list(p_values),
        logical_error_rates=logical_rates,
        x_error_rates=x_rates,
        z_error_rates=z_rates,
        n_shots_per_p=n_shots_per_p,
        code_name=getattr(code, "name", str(code)),
        benchmark_results=benchmark_results,
    )


def compare_codes(
    codes: List,
    noise_model_factory: Callable[[float], Callable[[StabilizerState], None]],
    decoder_factory: Callable,
    p_values: List[float],
    n_shots_per_p: int,
    *,
    seed: Optional[int] = None,
    verbose: bool = True,
) -> Dict[str, ThresholdScanResult]:
    """
    Run threshold_scan for multiple codes and return results keyed by code name.
    """
    results: Dict[str, ThresholdScanResult] = {}
    for i, code in enumerate(codes):
        code_seed = None if seed is None else seed + 100 * i
        code_name = getattr(code, "name", f"code_{i}")
        if verbose:
            print(f"\n=== {code_name} ===")
        results[code_name] = threshold_scan(
            code,
            noise_model_factory=noise_model_factory,
            decoder=decoder_factory(code),
            p_values=p_values,
            n_shots_per_p=n_shots_per_p,
            seed=code_seed,
            verbose=verbose,
        )
    return results


def build_lookup_decoder(
    code,
    noise_model_factory: Optional[Callable] = None,
    *,
    max_errors: int = 1,
) -> Callable[[List[int]], List[Tuple[int, str]]]:
    """
    Build a minimum-weight lookup-table decoder by syndrome enumeration.
    """
    _ = noise_model_factory
    if max_errors < 0:
        raise ValueError(f"max_errors must be non-negative, got {max_errors}")

    n = code.n
    table: Dict[Tuple[int, ...], List[Tuple[int, str]]] = {}
    paulis = ["X", "Y", "Z"]

    state = StabilizerState.zero(code.n)
    code.encode(state)
    table[tuple(code.read_syndrome(state))] = []

    for weight in range(1, max_errors + 1):
        for qubit_combo in itertools.combinations(range(n), weight):
            for pauli_combo in itertools.product(paulis, repeat=weight):
                state = StabilizerState.zero(code.n)
                code.encode(state)

                correction = list(zip(qubit_combo, pauli_combo))
                for q, p in correction:
                    if p == "X":
                        state.x(q)
                    elif p == "Y":
                        state.y(q)
                    elif p == "Z":
                        state.z(q)

                syndrome = tuple(code.read_syndrome(state))
                if syndrome not in table or len(correction) < len(table[syndrome]):
                    table[syndrome] = correction

    def decoder(syndrome: List[int]) -> List[Tuple[int, str]]:
        return table.get(tuple(syndrome), [])

    return decoder


def _combined_error_type(has_x: bool, has_z: bool) -> str:
    if has_x and has_z:
        return "Y"
    if has_x:
        return "X"
    if has_z:
        return "Z"
    return "I"
