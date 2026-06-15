import pytest

from stabilizer_python import CNOTGate, HGate, QuantumSimulator
from stabilizer_python.tableau import StabilizerState


def test_stabilizer_state_rejects_out_of_range_qubit():
    st = StabilizerState.zero(2)
    with pytest.raises(ValueError, match="q=2 out of range"):
        st.h(2)


def test_stabilizer_state_rejects_negative_qubit():
    st = StabilizerState.zero(2)
    with pytest.raises(ValueError, match="q=-1 out of range"):
        st.x(-1)


def test_stabilizer_state_cnot_rejects_bad_control():
    st = StabilizerState.zero(2)
    with pytest.raises(ValueError, match="control=2 out of range"):
        st.cnot(2, 0)


def test_stabilizer_state_measure_rejects_bad_qubit():
    st = StabilizerState.zero(2)
    with pytest.raises(ValueError, match="q=3 out of range"):
        st.measure_z(3)


def test_tableau_invariants_hold_for_bell_state():
    st = StabilizerState.zero(2)
    st.h(0)
    st.cnot(0, 1)
    st._check_tableau_invariants()


def test_simulator_rejects_out_of_range_qubit():
    sim = QuantumSimulator(2)
    with pytest.raises(ValueError, match="Gate h: qubit 2 out of range"):
        sim.apply(HGate, [2])


def test_simulator_rejects_duplicate_qubits():
    sim = QuantumSimulator(2)
    with pytest.raises(ValueError, match="duplicate qubit indices"):
        sim.apply(CNOTGate, [0, 0])


def test_simulator_debug_mode_accepts_valid_clifford_circuit():
    sim = QuantumSimulator(2, debug=True)
    sim.apply(HGate, [0])
    sim.apply(CNOTGate, [0, 1])
    sim.measure_z(0)


def test_simulator_measure_rejects_out_of_range_qubit():
    sim = QuantumSimulator(2)
    with pytest.raises(ValueError, match="qubit=2 out of range"):
        sim.measure_z(2)
