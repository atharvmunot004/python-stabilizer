"""
Tests for shot-based syndrome sampling and threshold scan.
"""

from stabilizer_python import (
    CodeBenchmarkResult,
    ShotRecord,
    ThresholdScanResult,
    benchmark_code,
    build_lookup_decoder,
    threshold_scan,
)
from stabilizer_python.noise import apply_bit_flip_all, apply_depolarizing_all
from stabilizer_python.stabilizer_code import BitFlip3Code, PerfectCode, SteaneCode


def _bitflip3_decoder(syndrome):
    if syndrome == [1, 0]:
        return [(0, "X")]
    if syndrome == [1, 1]:
        return [(1, "X")]
    if syndrome == [0, 1]:
        return [(2, "X")]
    return []


def _trivial_decoder(syndrome):
    return []


def test_benchmark_result_fields():
    result = CodeBenchmarkResult(
        n_shots=100,
        n_logical_errors=5,
        logical_error_rate=0.05,
        n_x_errors=3,
        n_z_errors=2,
        x_error_rate=0.03,
        z_error_rate=0.02,
        elapsed_seconds=1.0,
        shots_per_second=100.0,
        seed=42,
    )
    assert result.n_shots == 100
    assert result.logical_error_rate == 0.05
    assert result.records == []


def test_benchmark_result_summary():
    result = CodeBenchmarkResult(
        n_shots=100,
        n_logical_errors=5,
        logical_error_rate=0.05,
        n_x_errors=3,
        n_z_errors=2,
        x_error_rate=0.03,
        z_error_rate=0.02,
        elapsed_seconds=1.0,
        shots_per_second=100.0,
        seed=42,
    )
    out = result.summary()
    assert "100" in out
    assert "0.0500" in out


def test_benchmark_result_repr():
    result = CodeBenchmarkResult(
        n_shots=50,
        n_logical_errors=2,
        logical_error_rate=0.04,
        n_x_errors=2,
        n_z_errors=0,
        x_error_rate=0.04,
        z_error_rate=0.0,
        elapsed_seconds=0.5,
        shots_per_second=100.0,
        seed=None,
    )
    r = repr(result)
    assert "CodeBenchmarkResult" in r
    assert "50" in r


def test_benchmark_code_zero_noise_zero_errors():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=50,
        seed=0,
    )
    assert result.n_shots == 50
    assert result.n_logical_errors == 0
    assert result.logical_error_rate == 0.0


def test_benchmark_code_perfect_decoder_low_errors():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: apply_bit_flip_all(st, p=0.05, qubits=[0, 1, 2]),
        decoder=_bitflip3_decoder,
        n_shots=200,
        seed=1,
    )
    assert result.logical_error_rate < 0.15


def test_benchmark_code_certain_noise_produces_errors():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: apply_bit_flip_all(st, p=0.5, qubits=[0, 1, 2]),
        decoder=_trivial_decoder,
        n_shots=100,
        seed=2,
    )
    assert result.n_logical_errors > 0


def test_benchmark_code_returns_correct_n_shots():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=77,
        seed=3,
    )
    assert result.n_shots == 77


def test_benchmark_code_reproducible_with_seed():
    kwargs = dict(
        code=BitFlip3Code,
        noise_model=lambda st: apply_bit_flip_all(st, p=0.1, qubits=[0, 1, 2]),
        decoder=_bitflip3_decoder,
        n_shots=50,
        seed=42,
    )
    r1 = benchmark_code(**kwargs)
    r2 = benchmark_code(**kwargs)
    assert r1.n_logical_errors == r2.n_logical_errors


def test_benchmark_code_timing_fields():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=10,
        seed=0,
    )
    assert result.elapsed_seconds >= 0.0
    assert result.shots_per_second >= 0.0


def test_benchmark_code_x_and_z_error_rates_sum():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: apply_depolarizing_all(st, p=0.3, qubits=[0, 1, 2]),
        decoder=_trivial_decoder,
        n_shots=100,
        seed=5,
    )
    assert result.n_x_errors + result.n_z_errors >= result.n_logical_errors
    assert result.logical_error_rate <= 1.0


def test_benchmark_code_record_shots_gives_records():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=10,
        seed=0,
        record_shots=True,
    )
    assert len(result.records) == 10
    for rec in result.records:
        assert isinstance(rec, ShotRecord)
        assert rec.logical_error_type in ("I", "X", "Y", "Z")
        assert rec.had_logical_error == (rec.logical_error_type != "I")


def test_benchmark_code_no_record_shots_by_default():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=10,
        seed=0,
    )
    assert result.records == []


def test_shot_record_syndrome_length():
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=5,
        seed=0,
        record_shots=True,
    )
    n_checks = BitFlip3Code.n - BitFlip3Code.k
    for rec in result.records:
        assert len(rec.syndrome) == n_checks


def test_benchmark_perfect_code_zero_noise():
    result = benchmark_code(
        PerfectCode,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=20,
        seed=7,
    )
    assert result.n_logical_errors == 0


def test_benchmark_steane_code_zero_noise():
    result = benchmark_code(
        SteaneCode,
        noise_model=lambda st: None,
        decoder=_trivial_decoder,
        n_shots=20,
        seed=8,
    )
    assert result.n_logical_errors == 0


def test_threshold_scan_returns_correct_structure():
    p_values = [0.01, 0.05, 0.10]
    result = threshold_scan(
        BitFlip3Code,
        noise_model_factory=lambda p: (
            lambda st: apply_bit_flip_all(st, p, qubits=[0, 1, 2])
        ),
        decoder=_bitflip3_decoder,
        p_values=p_values,
        n_shots_per_p=30,
        seed=10,
        verbose=False,
    )
    assert isinstance(result, ThresholdScanResult)
    assert result.p_values == p_values
    assert len(result.logical_error_rates) == 3
    assert len(result.benchmark_results) == 3
    assert result.n_shots_per_p == 30


def test_threshold_scan_rates_increase_with_noise():
    result = threshold_scan(
        BitFlip3Code,
        noise_model_factory=lambda p: (
            lambda st: apply_bit_flip_all(st, p, qubits=[0, 1, 2])
        ),
        decoder=_trivial_decoder,
        p_values=[0.01, 0.20],
        n_shots_per_p=100,
        seed=11,
        verbose=False,
    )
    assert result.logical_error_rates[1] >= result.logical_error_rates[0]


def test_threshold_scan_as_dict():
    p_values = [0.01, 0.05]
    result = threshold_scan(
        BitFlip3Code,
        noise_model_factory=lambda p: (lambda st: None),
        decoder=_trivial_decoder,
        p_values=p_values,
        n_shots_per_p=10,
        seed=12,
        verbose=False,
    )
    d = result.as_dict()
    assert set(d.keys()) == set(p_values)
    assert all(isinstance(v, float) for v in d.values())


def test_threshold_scan_summary_string():
    result = threshold_scan(
        BitFlip3Code,
        noise_model_factory=lambda p: (lambda st: None),
        decoder=_trivial_decoder,
        p_values=[0.01, 0.05],
        n_shots_per_p=5,
        seed=13,
        verbose=False,
    )
    out = result.summary()
    assert "Bit-flip" in out or "BitFlip" in out or "3" in out
    assert "0.0100" in out


def test_threshold_scan_repr():
    result = threshold_scan(
        BitFlip3Code,
        noise_model_factory=lambda p: (lambda st: None),
        decoder=_trivial_decoder,
        p_values=[0.01],
        n_shots_per_p=5,
        seed=14,
        verbose=False,
    )
    assert "ThresholdScanResult" in repr(result)


def test_lookup_decoder_no_error_returns_empty():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    assert decoder([0, 0]) == []


def test_lookup_decoder_single_x_error_q0():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    assert decoder([1, 0]) == [(0, "X")]


def test_lookup_decoder_single_x_error_q1():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    assert decoder([1, 1]) == [(1, "X")]


def test_lookup_decoder_single_x_error_q2():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    assert decoder([0, 1]) == [(2, "X")]


def test_lookup_decoder_unknown_syndrome_returns_empty():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    assert decoder([9, 9]) == []


def test_lookup_decoder_in_benchmark():
    decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)
    result = benchmark_code(
        BitFlip3Code,
        noise_model=lambda st: apply_bit_flip_all(st, p=0.03, qubits=[0, 1, 2]),
        decoder=decoder,
        n_shots=100,
        seed=20,
    )
    assert result.logical_error_rate < 0.20


def test_lookup_decoder_perfect_code():
    decoder = build_lookup_decoder(PerfectCode, max_errors=1)
    assert decoder([0, 0, 0, 0]) == []
    correction = decoder([1, 0, 1, 0])
    assert isinstance(correction, list)
