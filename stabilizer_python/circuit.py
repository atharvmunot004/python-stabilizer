from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from .gate import (
    CNOTGate,
    CPhaseGate,
    CRXGate,
    CRYGate,
    CRZGate,
    CSGate,
    CSdgGate,
    CSwapGate,
    CXGate,
    CYGate,
    CZGate,
    CHGate,
    CCXGate,
    CCZGate,
    DCXGate,
    ECRGate,
    FredkinGate,
    Gate,
    HGate,
    IGate,
    MCXGate,
    PhaseGate,
    RGate,
    RXGate,
    RXXGate,
    RYGate,
    RYYGate,
    RZGate,
    RZZGate,
    RZXGate,
    SGate,
    SdgGate,
    SXGate,
    SXdgGate,
    SwapGate,
    TGate,
    TdgGate,
    ToffoliGate,
    U1Gate,
    U2Gate,
    U3Gate,
    UGate,
    XGate,
    XXMinusYYGate,
    XXPlusYYGate,
    YGate,
    ZGate,
    iSwapGate,
)
from .simulator import QuantumSimulator
from .tableau import StabilizerState


@dataclass(frozen=True)
class Op:
    name: str
    targets: Tuple[int, ...]
    gate_obj: Optional[Gate] = None


class Circuit:
    """Lightweight fluent circuit builder."""

    def __init__(self, n_qubits: int):
        """Create an empty circuit with n_qubits qubits."""
        if n_qubits <= 0:
            raise ValueError("n_qubits must be >= 1")
        self.n_qubits = n_qubits
        self.ops: List[Op] = []

    def gate(self, g: Gate, qubits: list[int]) -> "Circuit":
        """Append a generic gate operation."""
        self.ops.append(Op(g.name, tuple(qubits), g))
        return self

    def h(self, q: int) -> "Circuit":
        """Append a Hadamard gate."""
        self.ops.append(Op("H", (q,)))
        return self

    def s(self, q: int) -> "Circuit":
        """Append an S gate."""
        self.ops.append(Op("S", (q,)))
        return self

    def sdg(self, q: int) -> "Circuit":
        """Append an S-dagger gate."""
        return self.gate(SdgGate, [q])

    def x(self, q: int) -> "Circuit":
        """Append an X gate."""
        self.ops.append(Op("X", (q,)))
        return self

    def y(self, q: int) -> "Circuit":
        """Append a Y gate."""
        return self.gate(YGate, [q])

    def z(self, q: int) -> "Circuit":
        """Append a Z gate."""
        self.ops.append(Op("Z", (q,)))
        return self

    def i(self, q: int) -> "Circuit":
        """Append an identity gate."""
        return self.gate(IGate, [q])

    def sx(self, q: int) -> "Circuit":
        """Append an SX gate."""
        return self.gate(SXGate, [q])

    def sxdg(self, q: int) -> "Circuit":
        """Append an SX-dagger gate."""
        return self.gate(SXdgGate, [q])

    def t(self, q: int) -> "Circuit":
        """Append a T gate."""
        return self.gate(TGate, [q])

    def tdg(self, q: int) -> "Circuit":
        """Append a T-dagger gate."""
        return self.gate(TdgGate, [q])

    def rx(self, theta: float, q: int) -> "Circuit":
        """Append an Rx gate."""
        return self.gate(RXGate(theta), [q])

    def ry(self, theta: float, q: int) -> "Circuit":
        """Append an Ry gate."""
        return self.gate(RYGate(theta), [q])

    def rz(self, theta: float, q: int) -> "Circuit":
        """Append an Rz gate."""
        return self.gate(RZGate(theta), [q])

    def p(self, lam: float, q: int) -> "Circuit":
        """Append a phase gate."""
        return self.gate(PhaseGate(lam), [q])

    def u1(self, lam: float, q: int) -> "Circuit":
        """Append a U1 gate."""
        return self.gate(U1Gate(lam), [q])

    def u2(self, phi: float, lam: float, q: int) -> "Circuit":
        """Append a U2 gate."""
        return self.gate(U2Gate(phi, lam), [q])

    def u3(self, theta: float, phi: float, lam: float, q: int) -> "Circuit":
        """Append a U3 gate."""
        return self.gate(U3Gate(theta, phi, lam), [q])

    def u(self, theta: float, phi: float, lam: float, q: int) -> "Circuit":
        """Append a U gate."""
        return self.gate(UGate(theta, phi, lam), [q])

    def r(self, theta: float, phi: float, q: int) -> "Circuit":
        """Append an R gate."""
        return self.gate(RGate(theta, phi), [q])

    def cnot(self, control: int, target: int) -> "Circuit":
        """Append a CNOT gate."""
        self.ops.append(Op("CNOT", (control, target)))
        return self

    def cx(self, control: int, target: int) -> "Circuit":
        """Append a CX gate."""
        return self.gate(CXGate, [control, target])

    def cy(self, control: int, target: int) -> "Circuit":
        """Append a CY gate."""
        return self.gate(CYGate, [control, target])

    def cz(self, control: int, target: int) -> "Circuit":
        """Append a CZ gate."""
        return self.gate(CZGate, [control, target])

    def ch(self, control: int, target: int) -> "Circuit":
        """Append a CH gate."""
        return self.gate(CHGate, [control, target])

    def swap(self, q1: int, q2: int) -> "Circuit":
        """Append a SWAP gate."""
        return self.gate(SwapGate, [q1, q2])

    def iswap(self, q1: int, q2: int) -> "Circuit":
        """Append an iSWAP gate."""
        return self.gate(iSwapGate, [q1, q2])

    def ecr(self, q1: int, q2: int) -> "Circuit":
        """Append an ECR gate."""
        return self.gate(ECRGate, [q1, q2])

    def dcx(self, q1: int, q2: int) -> "Circuit":
        """Append a DCX gate."""
        return self.gate(DCXGate, [q1, q2])

    def cs(self, control: int, target: int) -> "Circuit":
        """Append a controlled-S gate."""
        return self.gate(CSGate, [control, target])

    def csdg(self, control: int, target: int) -> "Circuit":
        """Append a controlled-S-dagger gate."""
        return self.gate(CSdgGate, [control, target])

    def crx(self, theta: float, control: int, target: int) -> "Circuit":
        """Append a controlled-Rx gate."""
        return self.gate(CRXGate(theta), [control, target])

    def cry(self, theta: float, control: int, target: int) -> "Circuit":
        """Append a controlled-Ry gate."""
        return self.gate(CRYGate(theta), [control, target])

    def crz(self, theta: float, control: int, target: int) -> "Circuit":
        """Append a controlled-Rz gate."""
        return self.gate(CRZGate(theta), [control, target])

    def cp(self, lam: float, control: int, target: int) -> "Circuit":
        """Append a controlled-phase gate."""
        return self.gate(CPhaseGate(lam), [control, target])

    def rxx(self, theta: float, q1: int, q2: int) -> "Circuit":
        """Append an RXX gate."""
        return self.gate(RXXGate(theta), [q1, q2])

    def ryy(self, theta: float, q1: int, q2: int) -> "Circuit":
        """Append an RYY gate."""
        return self.gate(RYYGate(theta), [q1, q2])

    def rzz(self, theta: float, q1: int, q2: int) -> "Circuit":
        """Append an RZZ gate."""
        return self.gate(RZZGate(theta), [q1, q2])

    def rzx(self, theta: float, q1: int, q2: int) -> "Circuit":
        """Append an RZX gate."""
        return self.gate(RZXGate(theta), [q1, q2])

    def xx_plus_yy(self, theta: float, beta: float, q1: int, q2: int) -> "Circuit":
        """Append an XXPlusYY gate."""
        return self.gate(XXPlusYYGate(theta, beta), [q1, q2])

    def xx_minus_yy(self, theta: float, beta: float, q1: int, q2: int) -> "Circuit":
        """Append an XXMinusYY gate."""
        return self.gate(XXMinusYYGate(theta, beta), [q1, q2])

    def ccx(self, control1: int, control2: int, target: int) -> "Circuit":
        """Append a Toffoli gate."""
        return self.gate(CCXGate, [control1, control2, target])

    def toffoli(self, control1: int, control2: int, target: int) -> "Circuit":
        """Append a Toffoli gate."""
        return self.gate(ToffoliGate, [control1, control2, target])

    def mcx(self, control1: int, control2: int, target: int) -> "Circuit":
        """Append a three-qubit MCX gate."""
        return self.gate(MCXGate, [control1, control2, target])

    def ccz(self, control1: int, control2: int, target: int) -> "Circuit":
        """Append a CCZ gate."""
        return self.gate(CCZGate, [control1, control2, target])

    def cswap(self, control: int, target1: int, target2: int) -> "Circuit":
        """Append a controlled-SWAP gate."""
        return self.gate(CSwapGate, [control, target1, target2])

    def fredkin(self, control: int, target1: int, target2: int) -> "Circuit":
        """Append a Fredkin gate."""
        return self.gate(FredkinGate, [control, target1, target2])

    def mz(self, q: int, key: Optional[str] = None) -> "Circuit":
        """Append a Z-basis measurement."""
        # key is stored as metadata-like op name suffix; simple + dependency-free.
        self.ops.append(Op("MZ" if key is None else f"MZ:{key}", (q,)))
        return self

    def extend(self, ops: Iterable[Op]) -> "Circuit":
        """Append existing operations."""
        self.ops.extend(list(ops))
        return self

    def run(self, state: StabilizerState | QuantumSimulator) -> List[int]:
        """Apply all operations and return measurement outcomes."""
        sim = state if isinstance(state, QuantumSimulator) else QuantumSimulator(state.n)
        if isinstance(state, StabilizerState):
            sim.tableau = state
        if sim.tableau.n < self.n_qubits:
            raise ValueError("State has fewer qubits than circuit")
        out: List[int] = []
        for op in self.ops:
            if op.gate_obj is not None:
                sim.apply(op.gate_obj, list(op.targets))
            elif op.name == "H":
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
                out.append(sim.measure_z(op.targets[0]))
            else:
                raise ValueError(f"Unknown op: {op.name}")
        return out

