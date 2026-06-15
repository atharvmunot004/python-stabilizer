"""
Tests for StabilizerDecomposition: statevector-free non-Clifford simulation.
"""
import cmath
import math

import pytest

from stabilizer_python import StabilizerDecomposition


def test_clifford_h_single_term():
    sd = StabilizerDecomposition(1)
    sd.h(0)
    assert sd.term_count == 1


def test_clifford_bell_single_term():
    sd = StabilizerDecomposition(2)
    sd.h(0).cnot(0, 1)
    assert sd.term_count == 1
    generators = sd.terms[0][1].stabilizer_strings()
    assert "+XX" in generators
    assert "+ZZ" in generators


def test_clifford_ghz_single_term():
    sd = StabilizerDecomposition(3)
    sd.h(0).cnot(0, 1).cnot(0, 2)
    assert sd.term_count == 1
    generators = sd.terms[0][1].stabilizer_strings()
    assert "+XXX" in generators


def test_t_gate_doubles_terms():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    assert sd.term_count == 2


def test_t_gate_on_z_eigenstate_no_split():
    sd = StabilizerDecomposition(1)
    sd.t(0)
    assert sd.term_count == 1
    assert abs(sd.terms[0][0] - 1.0) < 1e-10


def test_t_gate_on_plus_state_splits():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    assert sd.term_count == 2


def test_two_t_gates_at_most_four_terms():
    sd = StabilizerDecomposition(2)
    sd.h(0).h(1).t(0).t(1)
    assert sd.term_count <= 4


def test_t_count_tracks_correctly():
    sd = StabilizerDecomposition(2)
    assert sd.t_count == 0
    sd.h(0).t(0)
    assert sd.t_count == 1
    sd.t(1)
    assert sd.t_count == 2


def test_tdg_on_zero_no_split():
    sd = StabilizerDecomposition(1)
    sd.tdg(0)
    assert sd.term_count == 1
    assert abs(sd.terms[0][0] - 1.0) < 1e-10


def test_t_tdg_roundtrip_term_count_is_bounded():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0).tdg(0)
    assert sd.term_count <= 4


def test_t_gate_coefficient_magnitude():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    assert sd.term_count == 2
    for coeff, _ in sd.terms:
        assert abs(abs(coeff) - 1.0 / math.sqrt(2.0)) < 1e-10


def test_t_gate_coefficient_phase():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    phases = sorted(cmath.phase(coeff) for coeff, _ in sd.terms)
    diff = phases[1] - phases[0]
    assert abs(diff - math.pi / 4.0) < 1e-10


def test_measure_z_collapses_to_valid_branch():
    sd = StabilizerDecomposition(1)
    sd.h(0).t(0)
    outcome = sd.measure_z(0)
    assert outcome in (0, 1)
    assert sd.term_count == 1
    assert sd.terms[0][1].z_measurement_branch(0) == "deterministic"


def test_other_non_clifford_gates_raise():
    sd = StabilizerDecomposition(1)
    with pytest.raises(NotImplementedError):
        sd.rz(0, math.pi / 8.0)


def test_summary_contains_term_count():
    sd = StabilizerDecomposition(2)
    sd.h(0).t(0)
    output = sd.summary()
    assert "terms=" in output
    assert "Term 0" in output


def test_summary_contains_stabilizer_strings():
    sd = StabilizerDecomposition(1)
    sd.t(0)
    output = sd.summary()
    assert "+Z" in output

