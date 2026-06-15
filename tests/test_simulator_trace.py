from stabilizer_python import CNOTGate, HGate, QuantumSimulator, TGate
from stabilizer_python.statevector import Statevector
from stabilizer_python.tableau import StabilizerState


def test_trace_disabled_by_default():
    sim = QuantumSimulator(2)
    sim.apply(HGate, [0])
    assert sim.trace == []


def test_clifford_only_trace_stays_in_tableau():
    sim = QuantumSimulator(2, trace=True)
    sim.apply(HGate, [0])
    sim.apply(CNOTGate, [0, 1])

    assert len(sim.trace) == 2
    assert sim.trace[0].gate_name == "h"
    assert sim.trace[0].qubits == [0]
    assert sim.trace[0].params == []
    assert sim.trace[0].mode_before == "tableau"
    assert sim.trace[0].mode_after == "tableau"
    assert isinstance(sim.trace[0].snapshot, StabilizerState)
    assert sim.trace[1].gate_name == "cnot"
    assert sim.trace[1].mode_after == "tableau"


def test_hybrid_trace_records_mode_switch():
    sim = QuantumSimulator(2, trace=True)
    sim.apply(HGate, [0])
    sim.apply(CNOTGate, [0, 1])
    sim.apply(TGate, [0])

    assert len(sim.trace) == 3
    assert sim.trace[2].gate_name == "t"
    assert sim.trace[2].mode_before == "tableau"
    assert sim.trace[2].mode_after == "statevector"
    assert isinstance(sim.trace[2].snapshot, Statevector)


def test_trace_records_gate_params():
    import math

    sim = QuantumSimulator(1, trace=True)
    sim.apply("rz", [0], params=[math.pi / 4])

    assert len(sim.trace) == 1
    assert sim.trace[0].gate_name == "rz"
    assert sim.trace[0].params == [math.pi / 4]
    assert sim.trace[0].mode_after == "statevector"


def test_trace_snapshots_are_independent_copies():
    sim = QuantumSimulator(1, trace=True)
    sim.apply(HGate, [0])
    tableau_snapshot = sim.trace[0].snapshot
    tableau_snapshot.x(0)

    assert sim.tableau.format_chp_printstate() != tableau_snapshot.format_chp_printstate()


def test_trace_via_apply_string_name():
    sim = QuantumSimulator(1, trace=True)
    sim.apply("h", [0])

    assert len(sim.trace) == 1
    assert sim.trace[0].gate_name == "h"
    assert sim.trace[0].qubits == [0]
