from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tableau import StabilizerState
from stabilizer_python.tracing import TracedCircuit


def test_syndrome_circuit_trace_steps():
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)

    tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
    outcomes = tc.run(st)

    assert outcomes == [0, 0]
    assert len(tc.steps) == 6
    assert all(step.kind == "gate" for step in tc.steps[:2])
    assert tc.steps[2].kind == "measurement"
    assert tc.steps[2].outcome == 0
    assert tc.steps[2].measurement_branch == "deterministic"
    assert tc.steps[5].kind == "measurement"
    assert tc.steps[5].outcome == 0


def test_syndrome_circuit_trace_detects_x_error():
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)
    st.x(1)

    tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
    outcomes = tc.run(st)

    assert outcomes == [1, 1]


def test_trace_disabled_records_nothing():
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)

    tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=False)
    outcomes = tc.run(st)

    assert outcomes == [0, 0]
    assert tc.steps == []


def test_print_trace_runs_without_error(capsys):
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)

    tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
    tc.run(st)
    tc.print_trace()

    output = capsys.readouterr().out
    assert "Step 1: CNOT(0, 3)" in output
    assert "Step 3: MZ(3, key='s01')" in output
    assert "outcome=0 (deterministic)" in output
