"""
Tests for magic state characterisation and noisy stabilizer simulation.
"""
import math

import pytest

from stabilizer_python import (
    Circuit,
    NoisyStabilizerState,
    PauliChannel,
    StabilizerDecomposition,
    StabilizerState,
    stabilizer_entropy,
    stabilizer_extent,
    stabilizer_fidelity,
)


def test_extent_pure_stabilizer_state():
    sd = StabilizerDecomposition(1)
    sd.h(0)
    assert abs(stabilizer_extent(sd) - 1.0) < 1e-10


def test_extent_after_one_t_gate():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    assert abs(stabilizer_extent(sd) - 2.0) < 1e-10


def test_extent_zero_state():
    sd = StabilizerDecomposition(1)
    assert abs(stabilizer_extent(sd) - 1.0) < 1e-10


def test_entropy_pure_stabilizer_state():
    sd = StabilizerDecomposition(1)
    sd.h(0)
    assert abs(stabilizer_entropy(sd)) < 1e-10


def test_entropy_after_t_gate():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    assert abs(stabilizer_entropy(sd) - 1.0) < 1e-10


def test_entropy_increases_with_t_gates():
    sd1 = StabilizerDecomposition(2)
    sd1.h(0).h(1).t(0)
    e1 = stabilizer_entropy(sd1)

    sd2 = StabilizerDecomposition(2)
    sd2.h(0).h(1).t(0).t(1)
    e2 = stabilizer_entropy(sd2)

    assert e2 >= e1


def test_fidelity_pure_stabilizer():
    sd = StabilizerDecomposition(1)
    sd.h(0)
    f = stabilizer_fidelity(sd)
    assert abs(f - 1.0) < 1e-10


def test_fidelity_after_t_gate():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    f = stabilizer_fidelity(sd)
    assert f < 1.0
    assert f > 0.0


def test_fidelity_in_range():
    sd = StabilizerDecomposition(2)
    sd.h(0).h(1).t(0).t(1)
    f = stabilizer_fidelity(sd)
    assert 0.0 <= f <= 1.0


def test_noisy_init_single_state():
    ns = NoisyStabilizerState(2)
    assert ns.ensemble_size == 1
    assert abs(ns.ensemble[0].probability - 1.0) < 1e-10


def test_noisy_from_pure():
    st = StabilizerState.zero(2)
    Circuit(2).h(0).cnot(0, 1).run(st)
    ns = NoisyStabilizerState.from_pure(st)
    assert ns.ensemble_size == 1
    assert len(ns.ensemble[0].state.stabilizer_generators()) == 2


def test_noisy_clifford_gate_preserves_size():
    ns = NoisyStabilizerState(2)
    ns.h(0).cnot(0, 1)
    assert ns.ensemble_size == 1


def test_noisy_clifford_produces_correct_stabilizers():
    ns = NoisyStabilizerState(2)
    ns.h(0).cnot(0, 1)
    pauli_strings = ns.ensemble[0].state.stabilizer_strings()
    assert "+XX" in pauli_strings
    assert "+ZZ" in pauli_strings


def test_bit_flip_channel_branches():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=0.1)
    assert ns.ensemble_size == 2


def test_bit_flip_channel_probabilities():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=0.1)
    probs = sorted(weighted.probability for weighted in ns.ensemble)
    assert abs(probs[0] - 0.1) < 1e-10
    assert abs(probs[1] - 0.9) < 1e-10


def test_depolarising_channel_branches():
    ns = NoisyStabilizerState(1)
    ns.apply_depolarising(0, p=0.3)
    assert ns.ensemble_size == 4


def test_depolarising_probabilities_sum_to_one():
    ns = NoisyStabilizerState(1)
    ns.apply_depolarising(0, p=0.1)
    total = sum(weighted.probability for weighted in ns.ensemble)
    assert abs(total - 1.0) < 1e-10


def test_zero_error_no_branch():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=0.0)
    assert ns.ensemble_size == 1


def test_certain_error_single_branch():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=1.0)
    assert ns.ensemble_size == 1
    assert abs(ns.ensemble[0].probability - 1.0) < 1e-10


def test_invalid_probability_raises():
    ns = NoisyStabilizerState(1)
    with pytest.raises(ValueError):
        ns.apply_pauli_channel(0, p_x=0.5, p_y=0.5, p_z=0.5)


def test_negative_probability_raises():
    ns = NoisyStabilizerState(1)
    with pytest.raises(ValueError):
        ns.apply_bit_flip(0, p=-0.1)


def test_prune_removes_tiny_branches():
    ns = NoisyStabilizerState(1)
    ns.apply_depolarising(0, p=1e-15)
    ns.prune(threshold=1e-10)
    assert ns.ensemble_size == 1


def test_dominant_state_is_most_probable():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=0.1)
    dominant = ns.dominant_state()
    assert dominant.n == 1
    assert ns.dominant_probability() > 0.5


def test_noisy_measure_returns_0_or_1():
    ns = NoisyStabilizerState(1)
    ns.h(0)
    ns.apply_depolarising(0, p=0.05)
    outcome = ns.measure_z(0)
    assert outcome in (0, 1)


def test_noisy_measure_collapses_ensemble():
    ns = NoisyStabilizerState(1)
    ns.apply_depolarising(0, p=0.1)
    ns.measure_z(0)
    assert ns.ensemble_size >= 1
    total_prob = sum(weighted.probability for weighted in ns.ensemble)
    assert abs(total_prob - 1.0) < 1e-10


def test_pauli_channel_depolarising_factory():
    channel = PauliChannel.depolarising(p=0.12)
    assert abs(channel.p_x - 0.04) < 1e-10
    assert abs(channel.p_y - 0.04) < 1e-10
    assert abs(channel.p_z - 0.04) < 1e-10
    assert "depolarising" in channel.name


def test_pauli_channel_bit_flip_factory():
    channel = PauliChannel.bit_flip(p=0.05)
    assert abs(channel.p_x - 0.05) < 1e-10
    assert abs(channel.p_y) < 1e-10
    assert abs(channel.p_z) < 1e-10


def test_pauli_channel_phase_flip_factory():
    channel = PauliChannel.phase_flip(p=0.05)
    assert abs(channel.p_x) < 1e-10
    assert abs(channel.p_y) < 1e-10
    assert abs(channel.p_z - 0.05) < 1e-10


def test_pauli_channel_bit_phase_flip_factory():
    channel = PauliChannel.bit_phase_flip(p=0.05)
    assert abs(channel.p_x) < 1e-10
    assert abs(channel.p_y - 0.05) < 1e-10
    assert abs(channel.p_z) < 1e-10


def test_pauli_channel_apply():
    channel = PauliChannel.bit_flip(p=0.1)
    ns = NoisyStabilizerState(1)
    channel.apply(ns, qubit=0)
    assert ns.ensemble_size == 2


def test_pauli_channel_apply_all():
    channel = PauliChannel.bit_flip(p=0.1)
    ns = NoisyStabilizerState(2)
    channel.apply_all(ns)
    assert ns.ensemble_size <= 4
    total_prob = sum(weighted.probability for weighted in ns.ensemble)
    assert abs(total_prob - 1.0) < 1e-10


def test_summary_output():
    ns = NoisyStabilizerState(1)
    ns.apply_bit_flip(0, p=0.1)
    output = ns.summary()
    assert "NoisyStabilizerState" in output
    assert "p=" in output


def test_entropy_zero_norm_raises():
    sd = StabilizerDecomposition(1)
    sd.terms = []
    with pytest.raises(ValueError):
        stabilizer_entropy(sd)


def test_invalid_noisy_state_size_raises():
    with pytest.raises(ValueError):
        NoisyStabilizerState(0)

