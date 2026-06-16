# Simulation Flow

This page follows a circuit from user code through tableau and statevector
execution.

---

## Circuit Execution

`Circuit` is an operation list. It does not own state.

```python
from stabilizer_python import Circuit, StabilizerState

state = StabilizerState.zero(2)
circuit = Circuit(2).h(0).cnot(0, 1).mz(0)
outcomes = circuit.run(state)
```

Execution flow:

```text
Circuit.run(target)
   |
   +--> target is StabilizerState
   |       |
   |       +--> create QuantumSimulator(target.n)
   |       +--> set sim.tableau = target
   |       +--> operations mutate the original tableau
   |
   +--> target is QuantumSimulator
           |
           +--> reuse existing simulator mode and state
```

For every operation:

1. If `op.gate_obj` is present, call `sim.apply(gate_obj, targets)`.
2. If `op.name` is a built-in fixed operation, map it to the corresponding gate.
3. If `op.name` starts with `MZ`, call `sim.measure_z(target)`.
4. Append measurement outcomes to the return list.

---

## NoisyCircuit Execution

`NoisyCircuit` subclasses `Circuit` and injects sampled noise during execution
when the target is a `StabilizerState`.

```text
NoisyCircuit.run(state)
   |
   +--> for each Clifford gate:
   |       |
   |       +--> apply the gate to the tableau
   |       +--> apply depolarizing noise to touched qubits with gate_error
   |
   +--> for each MZ operation:
           |
           +--> measure the physical qubit normally
           +--> flip the returned classical bit with meas_error
```

This is circuit-level noise for concrete Clifford circuits. The code-level
benchmark loop uses explicit `noise_model(state)` callables instead.

---

## Tableau Mode

In tableau mode, Clifford gates are cheap and exact.

```text
Gate is Clifford
   |
   v
QuantumSimulator.apply_gate(...)
   |
   v
StabilizerState.h/s/cnot/...
   |
   v
Update all 2n tableau rows
```

Examples:

- `H(q)` swaps X and Z bits in column `q`; rows with `Y` flip phase.
- `S(q)` XORs X into Z in column `q`; input `Y` rows flip phase.
- `CNOT(c,t)` updates both columns and applies the Aaronson-Gottesman phase condition.
- `X`, `Y`, and `Z` gates only flip row phases; they do not change Pauli support.

The algebra behind these updates is derived in
[Gate Operation Rules](../theory/gate-rules.md).

---

## Statevector Mode

The first non-Clifford operation forces dense simulation.

```text
Gate is non-Clifford
   |
   v
_switch_to_statevector()
   |
   +--> tableau_to_statevector(tableau)
   +--> sim.sv = converted state
   +--> sim.mode = "statevector"
   |
   v
Statevector.apply_gate(gate, qubits)
```

The conversion applies stabilizer projectors `(I + g_i) / 2` to produce the
unique vector represented by the tableau. After conversion, every later gate is
applied as a matrix, even if it is Clifford.

This is intentionally one-way. The project does not currently synthesize a
tableau back from an arbitrary dense statevector.

---

## Measurement Flow

### Tableau Measurement

```text
measure_z(q)
   |
   +--> validate q
   |
   +--> does any stabilizer row have X/Y on q?
          |
          +--> no: deterministic branch
          |       |
          |       +--> solve for stabilizer product equal to ±Z_q
          |       +--> return phase bit
          |
          +--> yes: random branch
                  |
                  +--> sample 0 or 1
                  +--> clear anticommuting rows by row multiplication
                  +--> install ±Z_q as a new stabilizer
                  +--> set +X_q as the matching destabilizer
```

### Statevector Measurement

```text
Statevector.measure_z(q)
   |
   +--> compute probability of q=0 and q=1
   +--> sample outcome
   +--> zero amplitudes inconsistent with outcome
   +--> renormalize
```

---

## Trace Flow

`QuantumSimulator(trace=True)` records snapshots after gate application.

```python
from stabilizer_python import QuantumSimulator

sim = QuantumSimulator(2, trace=True)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])

for step in sim.trace:
    print(step.gate_name, step.mode_before, step.mode_after)
```

Each trace step includes:

- gate name
- qubit targets
- parameters
- mode before
- mode after
- snapshot

Snapshot type:

| Mode after gate | Snapshot |
|---|---|
| `"tableau"` | `StabilizerState.copy()` |
| `"statevector"` | statevector copy |

---

## Debug Flow

`QuantumSimulator(debug=True)` runs `_check_tableau_invariants()` after
tableau-mode Clifford gates and Z measurements.

The invariant check validates:

- stabilizer rows commute pairwise
- stabilizer rows are independent over GF(2)

---

## Benchmark Flow

For decoder benchmarking, the package uses a code-level shot loop rather than a
single circuit object:

```text
benchmark_code(...)
   |
   +--> fresh StabilizerState.zero(code.n)
   +--> code.encode(state)
   +--> sampled Pauli noise mutates state
   +--> code.read_syndrome(state)
   +--> decoder maps syndrome to corrections
   +--> Pauli corrections mutate state
   +--> EncodedState checks residual logical errors
```

The separation keeps decoders independent from circuits: a decoder only sees a
syndrome and returns `(qubit, pauli)` corrections.

Debug mode is meant for development and tests. It is not needed for ordinary
simulation.

---

## QEC Flow

For modern code objects:

```text
StabilizerCode.zero_state()
   |
   +--> full stabilizer list = checks + logical Zs
   +--> StabilizerState.from_stabilizer_list(...)
   |
   v
code.read_syndrome(state)
   |
   +--> strip signs from checks
   +--> syndrome.read_syndrome(...)
   +--> add temporary ancilla
   +--> mixed parity checks
   +--> remove temporary ancilla
```

For legacy examples:

```text
codes.BitFlip3Code.encoder_circuit()
   |
   +--> explicit CNOT circuit
   |
   v
codes.BitFlip3Code.measure_syndrome(...)
   |
   +--> direct CNOT/measure/reset ancilla logic
```

Both paths use the same `StabilizerState` tableau operations underneath.
