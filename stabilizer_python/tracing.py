from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .circuit import Circuit, Op
from .gate import CNOTGate, HGate, SGate, XGate, ZGate
from .simulator import QuantumSimulator
from .tableau import StabilizerState


@dataclass(frozen=True)
class TraceStep:
    """One recorded step in a traced circuit execution."""

    index: int
    op_label: str
    kind: str
    state: StabilizerState
    outcome: Optional[int] = None
    measurement_branch: Optional[str] = None


def _format_op_label(op: Op) -> str:
    if op.name.startswith("MZ"):
        if ":" in op.name:
            key = op.name.split(":", 1)[1]
            return f"MZ({op.targets[0]}, key={key!r})"
        return f"MZ({op.targets[0]})"
    if len(op.targets) == 1:
        return f"{op.name}({op.targets[0]})"
    if len(op.targets) == 2:
        return f"{op.name}({op.targets[0]}, {op.targets[1]})"
    joined = ", ".join(str(q) for q in op.targets)
    return f"{op.name}({joined})"


def _apply_op(sim: QuantumSimulator, op: Op) -> Optional[int]:
    if op.gate_obj is not None:
        sim.apply_gate(op.gate_obj, list(op.targets))
        return None
    if op.name == "H":
        sim.apply(HGate, [op.targets[0]])
    elif op.name == "S":
        sim.apply(SGate, [op.targets[0]])
    elif op.name == "X":
        sim.apply(XGate, [op.targets[0]])
    elif op.name == "Z":
        sim.apply(ZGate, [op.targets[0]])
    elif op.name == "CNOT":
        c, t = op.targets
        sim.apply(CNOTGate, [c, t])
    elif op.name.startswith("MZ"):
        return sim.measure_z(op.targets[0])
    else:
        raise ValueError(f"Unknown op: {op.name}")
    return None


class TracedCircuit:
    """
    Run a Circuit while optionally recording the tableau after every gate and
    measurement. Intended for step-by-step QEC syndrome extraction demos.
    """

    def __init__(self, circuit: Circuit, trace: bool = True):
        self.circuit = circuit
        self.trace = trace
        self.steps: List[TraceStep] = []

    def run(self, state: StabilizerState) -> List[int]:
        """Apply the wrapped circuit to state and return measurement outcomes."""
        if state.n < self.circuit.n_qubits:
            raise ValueError("State has fewer qubits than circuit")

        sim = QuantumSimulator(state.n)
        sim.tableau = state
        self.steps = []
        outcomes: List[int] = []

        for index, op in enumerate(self.circuit.ops, start=1):
            op_label = _format_op_label(op)
            if op.name.startswith("MZ"):
                branch = sim.tableau.z_measurement_branch(op.targets[0])
                outcome = _apply_op(sim, op)
                assert outcome is not None
                outcomes.append(outcome)
                if self.trace:
                    if sim.mode != "tableau":
                        raise ValueError(
                            "TracedCircuit tracing requires Clifford operations in tableau mode"
                        )
                    self.steps.append(
                        TraceStep(
                            index=index,
                            op_label=op_label,
                            kind="measurement",
                            state=sim.tableau.copy(),
                            outcome=outcome,
                            measurement_branch=branch,
                        )
                    )
                continue

            _apply_op(sim, op)
            if self.trace:
                if sim.mode != "tableau":
                    raise ValueError(
                        "TracedCircuit tracing requires Clifford operations in tableau mode"
                    )
                self.steps.append(
                    TraceStep(
                        index=index,
                        op_label=op_label,
                        kind="gate",
                        state=sim.tableau.copy(),
                    )
                )

        return outcomes

    def print_trace(self) -> None:
        """Print every recorded step: operation, measurement info, and tableau."""
        if not self.steps:
            print("(no trace recorded)")
            return

        for step in self.steps:
            print(f"Step {step.index}: {step.op_label}")
            if step.kind == "measurement":
                print(
                    f"  outcome={step.outcome} ({step.measurement_branch})"
                )
            print(step.state.format_chp_printstate())
            print()
