from __future__ import annotations

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
from .statevector import Statevector, tableau_to_statevector
from .tableau import StabilizerState


class QuantumSimulator:
    """Hybrid simulator that routes Clifford gates to tableau and others to statevector."""

    def __init__(self, n: int):
        """Create an n-qubit simulator initialized to |0...0>."""
        self.n = n
        self.mode = "tableau"
        self.tableau = StabilizerState.zero(n)
        self.sv: Statevector | None = None

    def apply(self, gate: Gate | str, qubits: list[int], params: list[float] | None = None) -> None:
        """Apply a gate object or gate name to the simulator state."""
        gate_obj = gate if isinstance(gate, Gate) else self._gate_from_name(gate, params)
        self.apply_gate(gate_obj, qubits)

    def apply_gate(self, gate: Gate, qubits: list[int]) -> None:
        """Apply a Gate object to the simulator state."""
        method_names = {
            "h": "h",
            "s": "s",
            "sdg": "sdg",
            "x": "x",
            "y": "y",
            "z": "z",
            "sx": "sx",
            "sxdg": "sxdg",
            "cx": "cnot",
            "cnot": "cnot",
            "cz": "cz",
            "cy": "cy",
            "swap": "swap",
            "i": "i",
        }
        if gate.is_clifford and self.mode == "tableau" and gate.name in method_names:
            getattr(self.tableau, method_names[gate.name])(*qubits)
            return
        self._switch_to_statevector()
        if self.sv is None:
            raise RuntimeError("statevector backend is not initialized")
        self.sv.apply_gate(gate, qubits)

    def _gate_from_name(self, name: str, params: list[float] | None = None) -> Gate:
        """Build a Gate object from a local gate name and optional parameters."""
        fixed = {
            "i": IGate,
            "h": HGate,
            "x": XGate,
            "y": YGate,
            "z": ZGate,
            "s": SGate,
            "sdg": SdgGate,
            "sx": SXGate,
            "sxdg": SXdgGate,
            "t": TGate,
            "tdg": TdgGate,
            "cx": CXGate,
            "cnot": CNOTGate,
            "cy": CYGate,
            "cz": CZGate,
            "ch": CHGate,
            "swap": SwapGate,
            "iswap": iSwapGate,
            "ecr": ECRGate,
            "dcx": DCXGate,
            "cs": CSGate,
            "csdg": CSdgGate,
            "ccx": CCXGate,
            "toffoli": ToffoliGate,
            "ccz": CCZGate,
            "cswap": CSwapGate,
            "fredkin": FredkinGate,
            "mcx": MCXGate,
        }
        factories = {
            "rx": (RXGate, 1),
            "ry": (RYGate, 1),
            "rz": (RZGate, 1),
            "p": (PhaseGate, 1),
            "u1": (U1Gate, 1),
            "u2": (U2Gate, 2),
            "u3": (U3Gate, 3),
            "u": (UGate, 3),
            "r": (RGate, 2),
            "crx": (CRXGate, 1),
            "cry": (CRYGate, 1),
            "crz": (CRZGate, 1),
            "cp": (CPhaseGate, 1),
            "rxx": (RXXGate, 1),
            "ryy": (RYYGate, 1),
            "rzz": (RZZGate, 1),
            "rzx": (RZXGate, 1),
            "xx_plus_yy": (XXPlusYYGate, 2),
            "xx_minus_yy": (XXMinusYYGate, 2),
        }
        if name in fixed:
            return fixed[name]
        if name not in factories:
            raise ValueError("Unknown gate: {}".format(name))
        values = [] if params is None else params
        factory, count = factories[name]
        if len(values) != count:
            raise ValueError("Gate {} expects {} parameter(s)".format(name, count))
        return factory(*values)

    def _switch_to_statevector(self) -> None:
        """Switch from tableau to statevector mode if needed."""
        if self.mode == "statevector":
            return
        self.sv = tableau_to_statevector(self.tableau)
        self.mode = "statevector"

    def measure_z(self, qubit: int) -> int:
        """Measure a qubit in the Z basis."""
        if self.mode == "tableau":
            return self.tableau.measure_z(qubit)
        if self.sv is None:
            raise RuntimeError("statevector backend is not initialized")
        return self.sv.measure_z(qubit)

    def statevector_snapshot(self) -> Statevector:
        """Return a statevector snapshot without forcing future statevector routing."""
        if self.mode == "statevector":
            if self.sv is None:
                raise RuntimeError("statevector backend is not initialized")
            return self.sv
        return tableau_to_statevector(self.tableau)

    def reset(self, qubit: int) -> None:
        """Reset a qubit to |0> by measuring Z and applying X if needed."""
        outcome = self.measure_z(qubit)
        if outcome == 1:
            self.apply_gate(XGate, [qubit])
