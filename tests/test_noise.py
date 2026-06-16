"""
Tests for single-shot Pauli noise channels and NoisyCircuit.
"""
import random

import pytest

from stabilizer_python import (
    Circuit,
    NoisyCircuit,
    StabilizerState,
    apply_bit_flip,
    apply_bit_flip_all,
    apply_depolarizing,
    apply_depolarizing_all,
    apply_pauli_channel,
    apply_pauli_channel_all,
    apply_phase_flip,
    run_shots,
)
from stabilizer_python.codes import BitFlip3Code


def test_apply_pauli_channel_certain_x_applies_x():
    st = StabilizerState.zero(1)
    error = apply_pauli_channel(st, 0, p_x=1.0, p_y=0.0, p_z=0.0)
    assert error == "X"
    assert st.measure_z(0) == 1


def test_apply_pauli_channel_certain_z_applies_z():
    st = StabilizerState.zero(1)
    error = apply_pauli_channel(st, 0, p_x=0.0, p_y=0.0, p_z=1.0)
    assert error == "Z"


def test_apply_pauli_channel_certain_y_applies_y():
    st = StabilizerState.zero(1)
    error = apply_pauli_channel(st, 0, p_x=0.0, p_y=1.0, p_z=0.0)
    assert error == "Y"


def test_apply_pauli_channel_zero_probs_applies_identity():
    st = StabilizerState.zero(1)
    stabs_before = st.stabilizer_strings()
    error = apply_pauli_channel(st, 0, p_x=0.0, p_y=0.0, p_z=0.0)
    assert error == "I"
    assert st.stabilizer_strings() == stabs_before


def test_apply_pauli_channel_returns_correct_string():
    random.seed(42)
    results = set()
    for _ in range(1000):
        st = StabilizerState.zero(1)
        results.add(apply_pauli_channel(st, 0, p_x=0.25, p_y=0.25, p_z=0.25))
    assert results.issubset({"I", "X", "Y", "Z"})


def test_apply_pauli_channel_negative_probability_raises():
    st = StabilizerState.zero(1)
    with pytest.raises(ValueError):
        apply_pauli_channel(st, 0, p_x=-0.1, p_y=0.0, p_z=0.0)


def test_apply_pauli_channel_probabilities_over_one_raises():
    st = StabilizerState.zero(1)
    with pytest.raises(ValueError):
        apply_pauli_channel(st, 0, p_x=0.5, p_y=0.5, p_z=0.5)


def test_apply_pauli_channel_bad_qubit_raises():
    st = StabilizerState.zero(2)
    with pytest.raises(ValueError):
        apply_pauli_channel(st, 5, p_x=0.1, p_y=0.0, p_z=0.0)


def test_apply_pauli_channel_empirical_x_rate():
    random.seed(0)
    n_trials = 5000
    count = 0
    for _ in range(n_trials):
        st = StabilizerState.zero(1)
        if apply_pauli_channel(st, 0, p_x=0.2, p_y=0.0, p_z=0.0) == "X":
            count += 1
    rate = count / n_trials
    assert abs(rate - 0.2) < 0.02, f"Expected ~0.2, got {rate}"


def test_apply_depolarizing_zero_noise_is_identity():
    st = StabilizerState.zero(2)
    stabs_before = st.stabilizer_strings()
    apply_depolarizing(st, 0, p=0.0)
    assert st.stabilizer_strings() == stabs_before


def test_apply_depolarizing_certain_error():
    random.seed(7)
    results = set()
    for _ in range(300):
        st = StabilizerState.zero(1)
        results.add(apply_depolarizing(st, 0, p=1.0))
    assert "X" in results
    assert "Y" in results
    assert "Z" in results
    assert "I" not in results


def test_apply_depolarizing_bad_probability_raises():
    st = StabilizerState.zero(1)
    with pytest.raises(ValueError):
        apply_depolarizing(st, 0, p=1.5)


def test_apply_bit_flip_always_returns_x_or_i():
    random.seed(1)
    results = set()
    for _ in range(100):
        st = StabilizerState.zero(1)
        results.add(apply_bit_flip(st, 0, p=0.5))
    assert results.issubset({"I", "X"})


def test_apply_phase_flip_always_returns_z_or_i():
    random.seed(2)
    results = set()
    for _ in range(100):
        st = StabilizerState.zero(1)
        results.add(apply_phase_flip(st, 0, p=0.5))
    assert results.issubset({"I", "Z"})


def test_apply_pauli_channel_all_returns_one_per_qubit():
    st = StabilizerState.zero(4)
    errors = apply_pauli_channel_all(st, p_x=0.1, p_y=0.1, p_z=0.1)
    assert len(errors) == 4
    assert all(e in ("I", "X", "Y", "Z") for e in errors)


def test_apply_depolarizing_all_returns_one_per_qubit():
    st = StabilizerState.zero(3)
    errors = apply_depolarizing_all(st, p=0.05)
    assert len(errors) == 3


def test_apply_pauli_channel_all_subset():
    st = StabilizerState.zero(5)
    errors = apply_pauli_channel_all(
        st, p_x=0.2, p_y=0.0, p_z=0.0, qubits=[0, 2, 4]
    )
    assert len(errors) == 3


def test_apply_depolarizing_all_zero_noise_is_identity():
    st = StabilizerState.zero(3)
    stabs_before = st.stabilizer_strings()
    apply_depolarizing_all(st, p=0.0)
    assert st.stabilizer_strings() == stabs_before


def test_noisy_circuit_constructs_cleanly():
    c = NoisyCircuit(3, gate_error=0.01, meas_error=0.001)
    assert c.gate_error == 0.01
    assert c.meas_error == 0.001
    assert c.n_qubits == 3


def test_noisy_circuit_bad_gate_error_raises():
    with pytest.raises(ValueError):
        NoisyCircuit(2, gate_error=1.5)


def test_noisy_circuit_bad_meas_error_raises():
    with pytest.raises(ValueError):
        NoisyCircuit(2, meas_error=-0.1)


def test_noisy_circuit_zero_noise_matches_clean_circuit():
    random.seed(99)
    st_clean = StabilizerState.zero(3)
    st_noisy = StabilizerState.zero(3)

    Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st_clean)
    NoisyCircuit(3, gate_error=0.0, meas_error=0.0).h(0).cnot(0, 1).cnot(
        0, 2
    ).run(st_noisy)

    assert st_clean.stabilizer_strings() == st_noisy.stabilizer_strings()


def test_noisy_circuit_returns_measurement_outcomes():
    st = StabilizerState.zero(2)
    c = NoisyCircuit(2, gate_error=0.0, meas_error=0.0)
    c.h(0).cnot(0, 1).mz(0).mz(1)
    outcomes = c.run(st)
    assert len(outcomes) == 2
    assert all(o in (0, 1) for o in outcomes)
    assert outcomes[0] == outcomes[1]


def test_noisy_circuit_measurement_error_can_flip_outcome():
    random.seed(42)
    flipped_count = 0
    for _ in range(50):
        st = StabilizerState.zero(1)
        c = NoisyCircuit(1, gate_error=0.0, meas_error=1.0)
        c.mz(0)
        outcomes = c.run(st)
        if outcomes[0] == 1:
            flipped_count += 1
    assert flipped_count == 50


def test_noisy_circuit_gate_error_changes_state_probabilistically():
    changed = 0
    for _ in range(50):
        st = StabilizerState.zero(1)
        NoisyCircuit(1, gate_error=1.0, meas_error=0.0).h(0).run(st)
        if st.stabilizer_strings() != ["+X"]:
            changed += 1
    assert changed > 0


def test_noisy_circuit_inherits_circuit_gate_methods():
    c = NoisyCircuit(3, gate_error=0.0)
    c.h(0).s(1).cnot(0, 2).mz(0)
    assert len(c.ops) == 4


def _bitflip3_encode(state: StabilizerState) -> None:
    BitFlip3Code.encoder_circuit().run(state)


def _bitflip3_decoder(syndrome: list) -> list:
    s01, s12 = syndrome[0], syndrome[1]
    if (s01, s12) == (1, 0):
        return [(0, "X")]
    if (s01, s12) == (1, 1):
        return [(1, "X")]
    if (s01, s12) == (0, 1):
        return [(2, "X")]
    return []


def _bitflip3_noise(p: float):
    def _apply(state: StabilizerState) -> None:
        apply_bit_flip_all(state, p, qubits=[0, 1, 2])

    return _apply


def test_run_shots_zero_noise_zero_errors():
    result = run_shots(
        encode_fn=_bitflip3_encode,
        check_operators=["ZZI", "IZZ"],
        decoder_fn=_bitflip3_decoder,
        noise_channel=_bitflip3_noise(p=0.0),
        n_shots=100,
        n_data=3,
        logical_x="+XXX",
        logical_z="+IIZ",
        seed=0,
    )
    assert result["logical_errors"] == 0
    assert result["logical_error_rate"] == 0.0
    assert result["n_shots"] == 100


def test_run_shots_high_noise_has_errors():
    result = run_shots(
        encode_fn=_bitflip3_encode,
        check_operators=["ZZI", "IZZ"],
        decoder_fn=_bitflip3_decoder,
        noise_channel=_bitflip3_noise(p=0.4),
        n_shots=200,
        n_data=3,
        logical_x="+XXX",
        logical_z="+IIZ",
        seed=1,
    )
    assert result["logical_errors"] > 0
    assert 0.0 < result["logical_error_rate"] <= 1.0


def test_run_shots_returns_correct_keys():
    result = run_shots(
        encode_fn=_bitflip3_encode,
        check_operators=["ZZI", "IZZ"],
        decoder_fn=_bitflip3_decoder,
        noise_channel=_bitflip3_noise(p=0.01),
        n_shots=10,
        n_data=3,
        seed=2,
    )
    assert "n_shots" in result
    assert "logical_errors" in result
    assert "logical_error_rate" in result
    assert "x_errors" in result
    assert "z_errors" in result
    assert result["n_shots"] == 10


def test_run_shots_reproducible_with_seed():
    kwargs = dict(
        encode_fn=_bitflip3_encode,
        check_operators=["ZZI", "IZZ"],
        decoder_fn=_bitflip3_decoder,
        noise_channel=_bitflip3_noise(p=0.05),
        n_shots=50,
        n_data=3,
        logical_z="+IIZ",
        seed=42,
    )
    r1 = run_shots(**kwargs)
    r2 = run_shots(**kwargs)
    assert r1["logical_errors"] == r2["logical_errors"]


def test_run_shots_no_logical_ops_still_runs():
    result = run_shots(
        encode_fn=_bitflip3_encode,
        check_operators=["ZZI", "IZZ"],
        decoder_fn=_bitflip3_decoder,
        noise_channel=_bitflip3_noise(p=0.1),
        n_shots=20,
        n_data=3,
        seed=3,
    )
    assert result["logical_errors"] == 0
    assert result["x_errors"] == 0
    assert result["z_errors"] == 0
