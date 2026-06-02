import numpy as np

from stabilizer_python import (
    CNOTGate,
    CRZGate,
    CCXGate,
    HGate,
    QuantumSimulator,
    RZGate,
    RZZGate,
    SGate,
    TGate,
)
from stabilizer_python.statevector import tableau_to_statevector
from stabilizer_python.tableau import StabilizerState


def _same_up_to_global_phase(left, right, tol=1e-10):
    left = np.asarray(left, dtype=np.complex128)
    right = np.asarray(right, dtype=np.complex128)
    idx = np.argmax(np.abs(right))
    if abs(right[idx]) < tol:
        return np.allclose(left, right, atol=tol)
    phase = left[idx] / right[idx]
    return np.allclose(left, phase * right, atol=tol)


def test_t_gate_on_plus_triggers_statevector():
    sim = QuantumSimulator(1)
    sim.apply(HGate, [0])
    sim.apply(TGate, [0])

    expected = np.array([1.0, np.exp(1j * np.pi / 4.0)]) / np.sqrt(2.0)
    assert sim.mode == "statevector"
    assert np.allclose(sim.sv.data, expected)


def test_rz_pi_on_zero_equals_z_up_to_global_phase():
    rz_sim = QuantumSimulator(1)
    z_sim = QuantumSimulator(1)

    rz_sim.apply(RZGate(np.pi), [0])
    z_sim.apply(SGate, [0])
    z_sim.apply(SGate, [0])

    assert _same_up_to_global_phase(rz_sim.sv.data, z_sim.statevector_snapshot().data)


def test_rz_pi_over_two_on_zero_equals_s_up_to_global_phase():
    rz_sim = QuantumSimulator(1)
    s_sim = QuantumSimulator(1)

    rz_sim.apply(RZGate(np.pi / 2.0), [0])
    s_sim.apply(SGate, [0])

    assert _same_up_to_global_phase(rz_sim.sv.data, s_sim.statevector_snapshot().data)


def test_h_t_h_matches_known_matrix():
    sim = QuantumSimulator(1)
    sim.apply(HGate, [0])
    sim.apply(TGate, [0])
    sim.apply(HGate, [0])

    h = HGate.matrix
    expected = h @ TGate.matrix @ h @ np.array([1.0, 0.0], dtype=np.complex128)
    assert np.allclose(sim.sv.data, expected)


def test_toffoli_flips_target_when_controls_are_one():
    sim = QuantumSimulator(3)
    sim.apply(CCXGate, [0, 1, 2])
    sim.apply(TGate, [0])
    sim.sv.data[:] = 0.0
    sim.sv.data[3] = 1.0

    sim.apply(CCXGate, [0, 1, 2])

    expected = np.zeros(8, dtype=np.complex128)
    expected[7] = 1.0
    assert np.allclose(sim.sv.data, expected)


def test_crz_pi_on_eleven_applies_controlled_phase():
    sim = QuantumSimulator(2)
    sim.apply(TGate, [0])
    sim.sv.data[:] = 0.0
    sim.sv.data[3] = 1.0

    sim.apply(CRZGate(np.pi), [0, 1])

    expected = np.zeros(4, dtype=np.complex128)
    expected[3] = 1j
    assert np.allclose(sim.sv.data, expected)


def test_rzz_pi_over_two_on_zero_zero_applies_phase():
    sim = QuantumSimulator(2)
    sim.apply(RZZGate(np.pi / 2.0), [0, 1])

    expected = np.zeros(4, dtype=np.complex128)
    expected[0] = np.exp(-1j * np.pi / 4.0)
    assert np.allclose(sim.sv.data, expected)


def test_hybrid_circuit_switches_and_measures():
    sim = QuantumSimulator(2)
    sim.apply(HGate, [0])
    assert sim.mode == "tableau"

    sim.apply(TGate, [0])
    assert sim.mode == "statevector"

    sim.apply(CNOTGate, [0, 1])
    outcome = sim.measure_z(0)
    assert sim.mode == "statevector"
    assert outcome in (0, 1)


def test_tableau_to_statevector_on_bell_state():
    state = StabilizerState.zero(2)
    state.h(0)
    state.cnot(0, 1)

    sv = tableau_to_statevector(state)

    expected = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    assert np.allclose(sv.data, expected)
