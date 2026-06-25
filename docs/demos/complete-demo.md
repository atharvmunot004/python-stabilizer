# python-stabilizer — Complete Feature Demo Guide

**Package:** `pip install git+https://github.com/atharvmunot004/python-stabilizer.git`  
**Docs:** https://atharvmunot004.github.io/python-stabilizer  
**Version:** 0.2.0

---

## Table of Contents

1. [Installation & Imports](#1-installation--imports)
2. [StabilizerState — Core Tableau](#2-stabilizerstate--core-tableau)
3. [Clifford Gates on the Tableau](#3-clifford-gates-on-the-tableau)
4. [Measurement & Reset](#4-measurement--reset)
5. [Ancilla Qubits](#5-ancilla-qubits)
6. [Inspection & Debug Output](#6-inspection--debug-output)
7. [Circuit Builder](#7-circuit-builder)
8. [Named QEC Code Instances](#8-named-qec-code-instances)
9. [General StabilizerCode Class](#9-general-stabilizercode-class)
10. [Syndrome Extraction](#10-syndrome-extraction)
11. [EncodedState — Logical Tracking](#11-encodedstate--logical-tracking)
12. [Noise Channels](#12-noise-channels)
13. [Decoder Benchmarking](#13-decoder-benchmarking)
14. [Hybrid Simulation — QuantumSimulator](#14-hybrid-simulation--quantumsimulator)
15. [Qiskit Interoperability](#15-qiskit-interoperability)
16. [StabilizerDecomposition — T-gate Simulation](#16-stabilizerdecomposition--t-gate-simulation)
17. [Mixed State — NoisyStabilizerState](#17-mixed-state--noisystabilizerstate)
18. [Step-by-Step Tracing](#18-step-by-step-tracing)
19. [Ancilla Register & Parity Checks](#19-ancilla-register--parity-checks)
20. [GF(2) Linear Algebra](#20-gf2-linear-algebra)
21. [Gate Objects](#21-gate-objects)
22. [Statevector Backend](#22-statevector-backend)
23. [Legacy codes.py Helpers](#23-legacy-codespy-helpers)
24. [Scale Demonstration](#24-scale-demonstration)

---

## 1. Installation & Imports

```python
# Install
# pip install git+https://github.com/atharvmunot004/python-stabilizer.git

# Core imports
from stabilizer_python import (
    # State & simulation
    StabilizerState,
    Circuit,
    QuantumSimulator,
    # QEC
    StabilizerCode,
    EncodedState,
    SyndromeExtractor,
    read_syndrome,
    # Named codes
    BitFlip3Code,
    PhaseFlip3Code,
    PerfectCode,
    SteaneCode,
    Shor9Code,
    SurfaceCode3,
    # Noise
    apply_pauli_channel, apply_depolarizing, apply_bit_flip,
    apply_phase_flip, apply_bit_phase_flip,
    apply_pauli_channel_all, apply_depolarizing_all,
    apply_bit_flip_all, apply_phase_flip_all,
    NoisyCircuit,
    # Benchmarking
    benchmark_code, threshold_scan, compare_codes, build_lookup_decoder,
    # Non-Clifford & decomposition
    StabilizerDecomposition,
    # Magic/mixed states
    NoisyStabilizerState, PauliChannel,
    stabilizer_fidelity, stabilizer_extent, stabilizer_entropy,
    # Ancilla
    AncillaRegister, mixed_parity_check, x_parity_check, z_parity_check,
    # Gates
    HGate, XGate, YGate, ZGate, SGate, TGate, CNOTGate, CZGate,
    RXGate, RYGate, RZGate, PhaseGate,
    # Linear algebra
    gaussian_elimination_gf2, rank_gf2,
    # Statevector
    Statevector,
    codes,
)
from stabilizer_python.statevector import tableau_to_statevector
from stabilizer_python.tracing import TracedCircuit, TraceStep
from stabilizer_python.noise import run_shots
import math, random
```

---

## 2. StabilizerState — Core Tableau

### 2.1 Constructors

```python
# Zero state |0...0>
st = StabilizerState.zero(3)
print(st.n)                      # 3
print(st.stabilizer_strings())   # ['+ZII', '+IZI', '+IIZ']
print(st.destabilizer_strings()) # ['+XII', '+IXI', '+IIX']

# From stabilizer generators directly
bell = StabilizerState.from_stabilizer_list(["+XX", "+ZZ"])
print(bell.stabilizer_strings())  # ['+XX', '+ZZ']

# With minus signs
minus_state = StabilizerState.from_stabilizer_list(["-Z"])
print(minus_state.stabilizer_strings())  # ['-Z']  → this is |1>

# Omitted sign defaults to +
st2 = StabilizerState.from_stabilizer_list(["XX", "ZZ"])
print(st2.stabilizer_strings())   # ['+XX', '+ZZ']

# Deep copy
original = StabilizerState.zero(2)
copy = original.copy()
copy.h(0)
print(original.stabilizer_strings())  # unchanged: ['+ZI', '+IZ']
print(copy.stabilizer_strings())      # modified:  ['+XI', '+IZ']
```

### 2.2 Direct Tableau Access

```python
st = StabilizerState.zero(2)

# Raw binary matrices (lists of lists)
print(st.x_mat)    # [[1,0],[0,1],[0,0],[0,0]] — X bits, all 2n rows
print(st.z_mat)    # [[0,0],[0,0],[1,0],[0,1]] — Z bits, all 2n rows
print(st.r_phase)  # [0, 0, 0, 0]             — sign bits

# n attribute
print(st.n)        # 2

# Rows 0..n-1 are destabilizers, rows n..2n-1 are stabilizers
# x_mat[0] = X bits of destabilizer 0 = [1, 0]  (+XI)
# z_mat[2] = Z bits of stabilizer 0  = [1, 0]   (+ZI)
```

### 2.3 Generator Accessors

```python
# Apply H+CNOT to get Bell state
st = StabilizerState.zero(2)
st.h(0); st.cnot(0, 1)

# As (phase_bit, x_row, z_row) tuples
for phase, x, z in st.stabilizer_generators():
    print(phase, x, z)
# 0 [1, 1] [0, 0]    → +XX
# 0 [0, 0] [1, 1]    → +ZZ

for phase, x, z in st.destabilizer_generators():
    print(phase, x, z)

# As signed Pauli strings
print(st.stabilizer_strings())    # ['+XX', '+ZZ']
print(st.destabilizer_strings())  # ['+ZI', '+IX']

# Both at once as a dict
print(st.tableau_dict())
# {'stabilizers': ['+XX', '+ZZ'], 'destabilizers': ['+ZI', '+IX']}
```

---

## 3. Clifford Gates on the Tableau

### 3.1 Single-Qubit Gates

```python
st = StabilizerState.zero(1)

# Hadamard: X↔Z, Y→-Y
st.h(0)
print(st.stabilizer_strings())   # ['+X']  |0> → |+>

# Phase / S: X→Y, Z→Z, Y→-X
st2 = StabilizerState.zero(1)
st2.h(0); st2.s(0)
print(st2.stabilizer_strings())  # ['+Y']  |+> → |+i>

# S-dagger: X→-Y, Z→Z, Y→X
st3 = StabilizerState.zero(1)
st3.h(0); st3.sdg(0)
print(st3.stabilizer_strings())  # ['-Y']  |+> → |-i>
st3.s_dagger(0)                  # alias for sdg

# Sqrt-X: X→X, Z→-Y, Y→Z
st4 = StabilizerState.zero(1)
st4.sx(0)
print(st4.stabilizer_strings())  # ['-Y']
st4.sqrt_x(0)                    # alias for sx

# Sqrt-X-dagger
st5 = StabilizerState.zero(1)
st5.sxdg(0)
print(st5.stabilizer_strings())  # ['+Y']
st5.sqrt_x_dagger(0)             # alias

# Pauli X: flips sign of Z and Y rows
st6 = StabilizerState.zero(1)
st6.x(0)
print(st6.stabilizer_strings())  # ['-Z']  |0> → |1>

# Pauli Y
st7 = StabilizerState.zero(1)
st7.y(0)
print(st7.stabilizer_strings())  # ['-Z']  |0> → |1> (up to global phase)

# Pauli Z: flips sign of X and Y rows
st8 = StabilizerState.zero(1)
st8.h(0); st8.z(0)
print(st8.stabilizer_strings())  # ['-X']  |+> → |->

# Identity: no-op
st9 = StabilizerState.zero(1)
st9.i(0)
print(st9.stabilizer_strings())  # ['+Z']  unchanged
```

### 3.2 Two-Qubit Gates

```python
# CNOT: control 0, target 1
st = StabilizerState.zero(2)
st.h(0)
st.cnot(0, 1)
print(st.stabilizer_strings())   # ['+XX', '+ZZ']  Bell state

# CX (alias for CNOT)
st2 = StabilizerState.zero(2)
st2.h(0); st2.cx(0, 1)
print(st2.stabilizer_strings())  # same as above

# CZ: H(t) + CNOT + H(t)
st3 = StabilizerState.zero(2)
st3.h(0); st3.h(1); st3.cz(0, 1)
print(st3.stabilizer_strings())  # ['+XZ', '+ZX']

# CY
st4 = StabilizerState.zero(2)
st4.h(0); st4.cy(0, 1)
print(st4.stabilizer_strings())

# SWAP: implemented as CNOT(a,b) CNOT(b,a) CNOT(a,b)
st5 = StabilizerState.zero(2)
st5.x(0)                         # |1> on qubit 0
print("before swap:", st5.stabilizer_strings())  # ['-ZI', '+IZ']
st5.swap(0, 1)
print("after swap: ", st5.stabilizer_strings())  # ['+ZI', '-IZ'] → |01>
```

### 3.3 Building Standard States

```python
# Bell states
def bell_phi_plus():
    st = StabilizerState.zero(2)
    st.h(0); st.cnot(0, 1)
    return st   # stabilizers: XX, ZZ

def bell_phi_minus():
    st = StabilizerState.zero(2)
    st.x(0); st.h(0); st.cnot(0, 1)
    return st   # stabilizers: XX, -ZZ

def bell_psi_plus():
    st = StabilizerState.zero(2)
    st.h(0); st.cnot(0, 1); st.x(1)
    return st   # stabilizers: -XX, ZZ

# GHZ state
def ghz(n):
    st = StabilizerState.zero(n)
    st.h(0)
    for q in range(1, n):
        st.cnot(0, q)
    return st

g = ghz(4)
print(g.stabilizer_strings())   # ['+XXXX', '+ZZI I', '+ZIZI', '+ZIIZ'] (pattern)

# |+> on every qubit
def all_plus(n):
    st = StabilizerState.zero(n)
    for q in range(n):
        st.h(q)
    return st

# Cluster state (1D)
def cluster_1d(n):
    st = all_plus(n)
    for q in range(n - 1):
        st.cz(q, q + 1)
    return st
```

---

## 4. Measurement & Reset

### 4.1 Z-basis measurement

```python
random.seed(42)

# Deterministic: |0> measured in Z always gives 0
st = StabilizerState.zero(1)
results = [st.copy().measure_z(0) for _ in range(10)]
print(results)   # [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Deterministic: |1> always gives 1
st1 = StabilizerState.zero(1)
st1.x(0)
results = [st1.copy().measure_z(0) for _ in range(10)]
print(results)   # [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

# Random: |+> gives 0 or 1 with equal probability
results = []
for _ in range(1000):
    st = StabilizerState.zero(1)
    st.h(0)
    results.append(st.measure_z(0))
print(f"P(0) = {results.count(0)/1000:.3f}")   # ≈ 0.500
```

### 4.2 Post-measurement state

```python
# After measuring Bell state — qubits become correlated
st = StabilizerState.zero(2)
st.h(0); st.cnot(0, 1)

outcome_q0 = st.measure_z(0)
print(f"q0={outcome_q0}")
print(st.stabilizer_strings())   # will show both qubits in same basis state

outcome_q1 = st.measure_z(1)
print(f"q1={outcome_q1}")
print(f"Always match: {outcome_q0 == outcome_q1}")  # True
```

### 4.3 z_measurement_branch — peek before measuring

```python
# Check whether an upcoming measurement will be deterministic or random
st = StabilizerState.zero(1)
print(st.z_measurement_branch(0))   # "deterministic"

st.h(0)
print(st.z_measurement_branch(0))   # "random"

# Useful for tracing and teaching
```

### 4.4 reset_z

```python
# Measure and apply X if needed — leaves qubit in |0>
random.seed(7)
st = StabilizerState.zero(1)
st.h(0)               # |+> — random measurement
outcome = st.reset_z(0)
print(f"measured {outcome}, qubit is now |0>")
print(st.stabilizer_strings())   # ['+Z']  always

# Used to recycle ancilla qubits in QEC circuits
```

### 4.5 Measuring multiple qubits

```python
# Measure all qubits in a GHZ state
random.seed(0)
outcomes = []
st = StabilizerState.zero(5)
st.h(0)
for q in range(1, 5):
    st.cnot(0, q)

for q in range(5):
    outcomes.append(st.measure_z(q))

print(outcomes)   # all 0 or all 1 — perfect GHZ correlation
assert len(set(outcomes)) == 1   # all same
```

---

## 5. Ancilla Qubits

### 5.1 Adding ancillas

```python
st = StabilizerState.zero(3)
print(f"n = {st.n}")   # 3

# Add |0> ancilla at the end
st.add_ancilla_zero()
print(f"n = {st.n}")   # 4
print(st.stabilizer_strings())  # last stabilizer is +IIIZ

# Add |+> ancilla
st.add_ancilla_plus()
print(f"n = {st.n}")   # 5
print(st.stabilizer_strings())  # last stabilizer is +IIIIX
```

### 5.2 Removing ancillas

```python
st = StabilizerState.zero(3)
st.add_ancilla_zero()       # ancilla at index 3
# ... use ancilla for parity check ...
st.measure_z(3)             # must measure first
st.reset_z(3)               # bring back to |0>
st.remove_ancilla(3)        # now back to 3 qubits
print(f"n = {st.n}")        # 3
```

---

## 6. Inspection & Debug Output

### 6.1 inspect() — unified entry point

```python
st = StabilizerState.zero(3)
Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st)   # GHZ

# Default (chp view only)
print(st.inspect())

# Select specific views
print(st.inspect(views=["chp"]))
print(st.inspect(views=["binary"]))
print(st.inspect(views=["phase"]))
print(st.inspect(views=["debug"]))           # all three combined
print(st.inspect(views=["stabilizers"]))     # bottom n rows only
print(st.inspect(views=["destabilizers"]))   # top n rows only

# Multiple views at once
print(st.inspect(views=["chp", "binary", "phase"]))

# Stabilizers + destabilizers together
print(st.inspect(views=["stabilizers", "destabilizers"]))

# Unknown view raises ValueError
try:
    st.inspect(views=["nonexistent"])
except ValueError as e:
    print(e)
```

### 6.2 Individual formatters

```python
# CHP-style output — destabilizers, separator, stabilizers
print(st.format_chp_printstate())

# Raw X and Z bit tables (2n × n each)
print(st.format_xz_binary_matrices())

# Phase-bit column (2n × 1)
print(st.format_phase_matrix())

# All combined in one block
print(st.format_tableau_debug())
```

### 6.3 Programmatic access vs string output

```python
st = StabilizerState.zero(2)
st.h(0); st.cnot(0, 1)

# As lists of strings
print(st.stabilizer_strings())    # ['+XX', '+ZZ']
print(st.destabilizer_strings())  # ['+ZI', '+IX']

# As dict
print(st.tableau_dict())
# {'stabilizers': ['+XX', '+ZZ'], 'destabilizers': ['+ZI', '+IX']}

# Raw tuples
for phase, x, z in st.stabilizer_generators():
    sign = "-" if phase else "+"
    pauli = "".join(
        ["I","X","Y","Z"][(x[i]<<1)|z[i]] for i in range(st.n)
    )
    print(f"{sign}{pauli}")
```

### 6.4 Tableau invariant check (debug mode)

```python
st = StabilizerState.zero(4)
Circuit(4).h(0).cnot(0,1).cnot(0,2).cnot(0,3).run(st)

# Asserts stabilizers are independent and mutually commuting
st._check_tableau_invariants()   # no output = all good
print("Invariants hold")
```

---

## 7. Circuit Builder

### 7.1 Basic chaining

```python
# Fluent builder — returns self for chaining
circuit = Circuit(3).h(0).cnot(0, 1).cnot(0, 2)

st = StabilizerState.zero(3)
circuit.run(st)
print(st.stabilizer_strings())   # GHZ stabilizers
```

### 7.2 All Clifford gate methods

```python
c = Circuit(4)

# Single-qubit Clifford
c.h(0).s(0).sdg(0).sx(0).sxdg(0).x(0).y(0).z(0).i(0)

# Two-qubit Clifford
c.cnot(0,1).cx(0,1).cy(0,1).cz(0,1).ch(0,1)
c.swap(0,1).iswap(0,1).ecr(0,1).dcx(0,1).cs(0,1).csdg(0,1)

# Three-qubit
c.ccx(0,1,2).toffoli(0,1,2).mcx(0,1,2).ccz(0,1,2).cswap(0,1,2).fredkin(0,1,2)
```

### 7.3 Non-Clifford gate methods (for QuantumSimulator)

```python
c = Circuit(3)

# Single-qubit non-Clifford
c.t(0).tdg(0)
c.rx(math.pi/4, 0).ry(math.pi/3, 1).rz(math.pi/6, 2)
c.p(math.pi/4, 0)          # phase gate
c.u(math.pi/2, 0, math.pi, 0)  # general single-qubit unitary
c.u2(0, math.pi, 0)
c.u3(math.pi/2, 0, math.pi, 0)
c.r(math.pi/4, math.pi/6, 0)

# Two-qubit parameterized
c.crx(math.pi/4, 0, 1)
c.cry(math.pi/3, 0, 1)
c.crz(math.pi/2, 0, 1)
c.cp(math.pi/4, 0, 1)
c.rxx(math.pi/4, 0, 1)
c.ryy(math.pi/4, 0, 1)
c.rzz(math.pi/4, 0, 1)
c.rzx(math.pi/4, 0, 1)
c.xx_plus_yy(math.pi/4, 0, 0, 1)
c.xx_minus_yy(math.pi/4, 0, 0, 1)
```

### 7.4 Measurements with keys

```python
st = StabilizerState.zero(3)
outcomes = (
    Circuit(3)
    .h(0).cnot(0,1).cnot(0,2)
    .mz(0, key="q0")
    .mz(1, key="q1")
    .mz(2, key="q2")
    .run(st)
)
print(outcomes)       # list of 3 outcomes, in order
print(len(outcomes))  # 3
```

### 7.5 extend() — composing circuits

```python
from stabilizer_python.circuit import Op

# Build sub-circuits and combine
encoder = Circuit(3).h(0).cnot(0,1).cnot(0,2)
measurer = Circuit(3).mz(0).mz(1).mz(2)

full = Circuit(3).extend(encoder.ops).extend(measurer.ops)

st = StabilizerState.zero(3)
outcomes = full.run(st)
print(outcomes)   # correlated GHZ measurement
```

### 7.6 Running on StabilizerState vs QuantumSimulator

```python
# On StabilizerState (Clifford only)
st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0,1).run(st)

# On QuantumSimulator (handles non-Clifford)
sim = QuantumSimulator(2)
Circuit(2).h(0).t(0).cnot(0,1).run(sim)
print(sim.mode)   # "statevector" — switched on T gate

# Circuit with state size check
try:
    st = StabilizerState.zero(2)
    Circuit(5).h(0).run(st)   # 5-qubit circuit on 2-qubit state
except ValueError as e:
    print(e)
```

### 7.7 Gate objects in circuits

```python
from stabilizer_python import HGate, CNOTGate

# Use Gate objects directly
c = Circuit(2)
c.gate(HGate, [0])
c.gate(CNOTGate, [0, 1])

st = StabilizerState.zero(2)
c.run(st)
print(st.stabilizer_strings())   # ['+XX', '+ZZ']
```

---

## 8. Named QEC Code Instances

```python
# All 6 named codes — top-level imports
from stabilizer_python import (
    BitFlip3Code, PhaseFlip3Code,
    PerfectCode, SteaneCode,
    Shor9Code, SurfaceCode3
)

# Each exposes the same API
codes_list = [BitFlip3Code, PhaseFlip3Code, PerfectCode,
              SteaneCode, Shor9Code, SurfaceCode3]

for code in codes_list:
    print(f"{code.name:30s}  n={code.n}  k={code.k}  generators={len(code.generators)}")
```

**Expected output:**
```
Bit-flip [[3,1,1]]             n=3  k=1  generators=2
Phase-flip [[3,1,1]]           n=3  k=1  generators=2
Perfect [[5,1,3]]              n=5  k=1  generators=4
Steane [[7,1,3]]               n=7  k=1  generators=6
Shor [[9,1,3]]                 n=9  k=1  generators=8
Rotated Surface [[9,1,3]]      n=9  k=1  generators=8
```

```python
# Generators
print(BitFlip3Code.generators)    # ['+ZZI', '+IZZ']
print(SteaneCode.generators)      # 6 CSS generators

# Logical operators
print(PerfectCode.logical_x())    # '+XXXXX'
print(PerfectCode.logical_z())    # '+ZZZZZ'
print(SteaneCode.logical_x(0))   # '+XXXXXXX'

# Distance
print(PerfectCode.distance())   # 3
print(SteaneCode.distance())    # 3
print(BitFlip3Code.distance())  # 1  (bit-flip only corrects X)

# Logical zero state
state = SteaneCode.zero_state()
print(f"n={state.n}")                        # 7
print(SteaneCode.read_syndrome(state))       # [0,0,0,0,0,0]  clean codeword

# Inject an error and check syndrome
state.x(3)
syn = SteaneCode.read_syndrome(state)
print(syn)   # non-zero — error detected
```

---

## 9. General StabilizerCode Class

### 9.1 Defining a custom code

```python
# Bit-flip by hand
my_code = StabilizerCode(
    n=3,
    k=1,
    generators=["+ZZI", "+IZZ"],
    name="My Bit-Flip [[3,1,1]]",
    logical_xs=["+XXX"],
    logical_zs=["+IIZ"],
)
print(my_code)

# Phase-flip by hand
phase_flip = StabilizerCode(
    n=3,
    k=1,
    generators=["+XXI", "+IXX"],
    logical_xs=["+IIX"],
    logical_zs=["+ZZZ"],
)

# [[4,2,2]] code — encodes 2 logical qubits
four_two_two = StabilizerCode(
    n=4,
    k=2,
    generators=["XXXX", "ZZZZ"],
    name="[[4,2,2]]",
)
print(four_two_two.k)   # 2
print(four_two_two.logical_x(0))
print(four_two_two.logical_x(1))
```

### 9.2 Validation errors

```python
# Wrong number of generators
try:
    StabilizerCode(n=3, k=1, generators=["+ZZI"])   # need 2
except ValueError as e:
    print(e)   # "Expected 2 generators ..."

# Anticommuting generators
try:
    StabilizerCode(n=2, k=0, generators=["+XX", "+ZI"])
except ValueError as e:
    print(e)   # "Generators 0 and 1 anticommute"

# Linearly dependent generators
try:
    StabilizerCode(n=3, k=1, generators=["+ZZI", "+ZZI"])
except ValueError as e:
    print(e)   # "Generators must have rank 2 ..."

# Identity stabilizer
try:
    StabilizerCode(n=2, k=0, generators=["+ZZ", "+II"])
except ValueError as e:
    print(e)
```

### 9.3 zero_state and encode

```python
# zero_state() builds |0_L> directly
state = PerfectCode.zero_state()
print(PerfectCode.read_syndrome(state))   # [0,0,0,0]  — clean

# encode() mutates an existing state
state2 = StabilizerState.zero(5)
PerfectCode.encode(state2)
print(PerfectCode.read_syndrome(state2))  # [0,0,0,0]

# zero_logical() classmethod — alternate syntax
state3 = StabilizerCode.zero_logical(SteaneCode)
print(SteaneCode.read_syndrome(state3))  # [0,0,0,0,0,0]

# encoding_circuit() — best-effort Clifford encoder
c = BitFlip3Code.encoding_circuit()
st = StabilizerState.zero(3)
c.run(st)
print(BitFlip3Code.read_syndrome(st))   # [0, 0]
```

### 9.4 Logical operators

```python
# Provided logical operators
print(SteaneCode.logical_x(0))   # '+XXXXXXX'
print(SteaneCode.logical_z(0))   # '+ZZZZZZZ'

# Computed logical operators (when not provided)
custom = StabilizerCode(n=3, k=1, generators=["+ZZI", "+IZZ"])
# Not provided in constructor — computed lazily
print(custom.logical_x(0))   # found by symplectic complement
print(custom.logical_z(0))

# k>1 codes
print(four_two_two.logical_x(0))
print(four_two_two.logical_x(1))
print(four_two_two.logical_z(0))
print(four_two_two.logical_z(1))

# Out of range
try:
    BitFlip3Code.logical_x(5)
except IndexError as e:
    print(e)
```

### 9.5 distance()

```python
# Exact minimum-weight logical operator search
for code in [BitFlip3Code, PerfectCode, SteaneCode]:
    print(f"{code.name}: d={code.distance()}")
```

---

## 10. Syndrome Extraction

### 10.1 StabilizerCode.read_syndrome()

```python
# Clean codeword → all zeros
state = BitFlip3Code.zero_state()
print(BitFlip3Code.read_syndrome(state))   # [0, 0]

# Inject errors and read syndrome
errors = {
    "none":  lambda st: None,
    "X on 0": lambda st: st.x(0),
    "X on 1": lambda st: st.x(1),
    "X on 2": lambda st: st.x(2),
    "Z on 0": lambda st: st.z(0),   # undetectable by bit-flip code
}

for name, inject in errors.items():
    state = BitFlip3Code.zero_state()
    inject(state)
    syn = BitFlip3Code.read_syndrome(state)
    print(f"{name:12s} → syndrome {syn}")
```

**Expected output:**
```
none         → syndrome [0, 0]
X on 0       → syndrome [1, 0]
X on 1       → syndrome [1, 1]
X on 2       → syndrome [0, 1]
Z on 0       → syndrome [0, 0]   ← undetectable, as expected
```

### 10.2 SyndromeExtractor — reusable rounds

```python
state = BitFlip3Code.zero_state()
extractor = BitFlip3Code.syndrome_extractor(state)

print(extractor.extract())   # [0, 0] — clean
state.x(2)
print(extractor.extract())   # [0, 1] — X error on qubit 2
print(extractor.n_checks())  # 2
```

### 10.3 read_syndrome() standalone function

```python
# Works on any state with any Pauli checks
state = StabilizerState.zero(4)
Circuit(4).h(0).cnot(0,1).cnot(0,2).cnot(0,3).run(state)   # GHZ-4

checks = ["ZZII", "IZZI", "IIZZ"]
print(read_syndrome(state, checks))   # [0, 0, 0] — GHZ is stabilized by ZZ pairs
```

---

## 11. EncodedState — Logical Tracking

### 11.1 Construction

```python
state = BitFlip3Code.zero_state()
encoded = EncodedState(state, BitFlip3Code)

# From explicit operators
encoded2 = EncodedState.from_logical_ops(
    state=StabilizerState.zero(3),
    logical_xs=["+XXX"],
    logical_zs=["+IIZ"],
    check_operators=["ZZI", "IZZ"],
    code_name="Custom BitFlip"
)
```

### 11.2 Logical readout

```python
state = BitFlip3Code.zero_state()
enc = EncodedState(state, BitFlip3Code)

# Eigenvalue (not a measurement — non-destructive)
print(enc.logical_z_eigenvalue())   # +1  (|0_L>)
print(enc.logical_x_eigenvalue())   # None — X is undetermined in |0_L>
print(enc.logical_state_string())   # '|0_L>'

# Measurement (returns bit: 0 for +1, 1 for -1)
print(enc.measure_logical_z())   # 0
```

### 11.3 Error detection

```python
state = BitFlip3Code.zero_state()
enc = EncodedState(state, BitFlip3Code)

state.x(1)   # inject X on qubit 1 — detectable, not logical

print(enc.has_logical_x_error())   # False — detectable, not a logical X
print(enc.has_logical_z_error())   # False
print(enc.logical_error_type())    # 'I'
print(enc.syndrome())              # [1, 1]
print(enc.is_valid_codeword())     # False

# Now inject a logical X (undetectable by Z-check code)
state2 = BitFlip3Code.zero_state()
enc2 = EncodedState(state2, BitFlip3Code)
enc2.apply_logical_x()             # applies XXX physically

# After intentional logical X, frame is updated — no error
print(enc2.has_logical_error())    # False
print(enc2.logical_state_string()) # '|1_L>'

# Unintentional logical X — flip physical without updating frame
state3 = BitFlip3Code.zero_state()
enc3 = EncodedState(state3, BitFlip3Code)
state3.x(0); state3.x(1); state3.x(2)   # manual XXX = logical X

print(enc3.has_logical_x_error())  # True — not in frame!
print(enc3.logical_error_type())   # 'X'
```

### 11.4 Logical gates

```python
state = SteaneCode.zero_state()
enc = EncodedState(state, SteaneCode)

print(enc.logical_state_string())   # '|0_L>'

enc.apply_logical_x()
print(enc.logical_state_string())   # '|1_L>'
print(enc.has_logical_error())      # False — intentional

enc.apply_logical_z()
print(enc.logical_state_string())   # '|1_L>' with Z applied

enc.apply_logical_y()
enc.apply_logical_h()   # swap X and Z logical labels

# summary()
print(enc.summary())
```

### 11.5 Multi-logical-qubit codes

```python
code = StabilizerCode(n=4, k=2, generators=["XXXX", "ZZZZ"])
state = code.zero_state()
enc = EncodedState(state, code)

print(enc.logical_z_eigenvalue(0))   # +1
print(enc.logical_z_eigenvalue(1))   # +1

enc.apply_logical_x(0)
print(enc.logical_state_string(0))   # '|1_L>'
print(enc.logical_state_string(1))   # '|0_L>'
```

---

## 12. Noise Channels

### 12.1 Single-qubit channels

```python
random.seed(0)
state = StabilizerState.zero(5)

# Custom Pauli channel
error = apply_pauli_channel(state, qubit=2, p_x=0.1, p_y=0.05, p_z=0.1)
print(f"Applied: {error}")   # one of 'I', 'X', 'Y', 'Z'

# Depolarizing: p/3 each for X, Y, Z
state = StabilizerState.zero(5)
error = apply_depolarizing(state, qubit=0, p=0.01)
print(f"Applied: {error}")

# Bit-flip: X with probability p
state = StabilizerState.zero(5)
error = apply_bit_flip(state, qubit=1, p=0.1)
print(f"Applied: {error}")  # 'X' or 'I'

# Phase-flip: Z with probability p
state = StabilizerState.zero(5)
error = apply_phase_flip(state, qubit=3, p=0.05)
print(f"Applied: {error}")  # 'Z' or 'I'

# Bit-phase flip: Y with probability p
state = StabilizerState.zero(5)
error = apply_bit_phase_flip(state, qubit=4, p=0.02)
print(f"Applied: {error}")  # 'Y' or 'I'
```

### 12.2 Multi-qubit channels (independent per qubit)

```python
state = StabilizerState.zero(7)

# Depolarize all qubits
errors = apply_depolarizing_all(state, p=0.01)
print(f"Errors: {errors}")   # list of 7 Pauli labels

# Bit-flip only qubits 0,1,2 (data qubits of a code)
state = SteaneCode.zero_state()
errors = apply_bit_flip_all(state, p=0.05, qubits=[0,1,2,3,4,5,6])
print(f"Errors: {errors}")

# Phase-flip all
errors = apply_phase_flip_all(state, p=0.02)

# Custom channel on all
errors = apply_pauli_channel_all(state, p_x=0.02, p_y=0.01, p_z=0.02)
```

### 12.3 NoisyCircuit

```python
# Injects depolarizing after every gate + bit-flips measurements
noisy = NoisyCircuit(n=2, gate_error=0.01, meas_error=0.02)
noisy.h(0).cnot(0, 1).mz(0).mz(1)

outcomes = []
for _ in range(100):
    st = StabilizerState.zero(2)
    outcomes.append(tuple(noisy.run(st)))

# Should be mostly (0,0) and (1,1) but with some noise-induced errors
correlated = sum(1 for o in outcomes if o[0] == o[1])
print(f"Correlated: {correlated}/100")   # ≈ 98 (some measurement errors)
```

### 12.4 Probability validation

```python
# Probabilities must be in [0,1]
try:
    apply_bit_flip(StabilizerState.zero(1), 0, p=1.5)
except ValueError as e:
    print(e)

# Custom channel probabilities must sum to ≤ 1
try:
    apply_pauli_channel(StabilizerState.zero(1), 0, p_x=0.5, p_y=0.5, p_z=0.5)
except ValueError as e:
    print(e)
```

---

## 13. Decoder Benchmarking

### 13.1 build_lookup_decoder

```python
# Enumerate all weight-1 errors and build syndrome → correction table
decoder = build_lookup_decoder(BitFlip3Code, max_errors=1)

# Test decoder on each syndrome
print(decoder([0, 0]))   # []          no correction
print(decoder([1, 0]))   # [(0, 'X')]  correct qubit 0
print(decoder([1, 1]))   # [(1, 'X')]  correct qubit 1
print(decoder([0, 1]))   # [(2, 'X')]  correct qubit 2
```

### 13.2 benchmark_code — single run

```python
from stabilizer_python.noise import apply_bit_flip_all

decoder = build_lookup_decoder(BitFlip3Code)

result = benchmark_code(
    BitFlip3Code,
    noise_model=lambda st: apply_bit_flip_all(st, p=0.05, qubits=[0,1,2]),
    decoder=decoder,
    n_shots=500,
    seed=42,
)

print(result.n_shots)            # 500
print(result.n_logical_errors)   # small number
print(f"Logical error rate: {result.logical_error_rate:.4f}")
print(f"X error rate:       {result.x_error_rate:.4f}")
print(f"Z error rate:       {result.z_error_rate:.4f}")
print(f"Throughput:         {result.shots_per_second:.0f} shots/s")
print(result.summary())
```

### 13.3 Per-shot records

```python
result = benchmark_code(
    BitFlip3Code,
    noise_model=lambda st: apply_bit_flip_all(st, p=0.10),
    decoder=decoder,
    n_shots=20,
    seed=0,
    record_shots=True,
)

for rec in result.records[:5]:
    print(f"shot {rec.shot_index}: syndrome={rec.syndrome}  "
          f"correction={rec.correction}  error={rec.logical_error_type}  "
          f"had_error={rec.had_logical_error}")
```

### 13.4 threshold_scan

```python
scan = threshold_scan(
    BitFlip3Code,
    noise_model_factory=lambda p: (
        lambda st: apply_bit_flip_all(st, p=p, qubits=[0,1,2])
    ),
    decoder=decoder,
    p_values=[0.01, 0.05, 0.10, 0.15, 0.20],
    n_shots_per_p=300,
    seed=1,
    verbose=True,
)

print(scan.summary())
print(scan.as_dict())    # {p: logical_error_rate}

# p_values and rates
for p, rate in zip(scan.p_values, scan.logical_error_rates):
    print(f"p_phys={p:.2f}  →  p_L={rate:.4f}")
```

### 13.5 compare_codes

```python
codes_to_compare = [BitFlip3Code, PerfectCode]
decoders = {
    BitFlip3Code.name: build_lookup_decoder(BitFlip3Code),
    PerfectCode.name:  build_lookup_decoder(PerfectCode),
}

results = compare_codes(
    codes_to_compare,
    noise_model_factory=lambda p: (lambda st: apply_depolarizing_all(st, p=p)),
    decoder_factory=lambda code: decoders[code.name],
    p_values=[0.01, 0.05, 0.10],
    n_shots_per_p=200,
    seed=2,
    verbose=False,
)

for name, scan in results.items():
    print(f"\n{name}")
    for p, rate in zip(scan.p_values, scan.logical_error_rates):
        print(f"  p={p:.2f}  p_L={rate:.4f}")
```

### 13.6 CodeBenchmarkResult fields

```python
# All fields on CodeBenchmarkResult
print(dir(result))
# n_shots, n_logical_errors, logical_error_rate
# n_x_errors, n_z_errors, x_error_rate, z_error_rate
# elapsed_seconds, shots_per_second, seed, records
```

---

## 14. Hybrid Simulation — QuantumSimulator

### 14.1 Tableau mode (Clifford only)

```python
sim = QuantumSimulator(3)
print(sim.mode)    # "tableau"
print(sim.n)       # 3

sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("cnot", [0, 2])
print(sim.mode)    # still "tableau"
print(sim.tableau.stabilizer_strings())   # GHZ stabilizers
```

### 14.2 Non-Clifford triggers statevector

```python
sim = QuantumSimulator(1)
sim.apply("h", [0])
print(sim.mode)   # "tableau"

sim.apply("t", [0])
print(sim.mode)   # "statevector" — switched!
print(sim.sv.to_dict())   # amplitudes in computational basis
```

### 14.3 apply() with gate names and params

```python
sim = QuantumSimulator(2)

# Fixed Clifford gates
sim.apply("h",    [0])
sim.apply("cnot", [0, 1])
sim.apply("s",    [0])
sim.apply("sdg",  [0])
sim.apply("x",    [1])
sim.apply("cz",   [0, 1])
sim.apply("swap", [0, 1])
sim.apply("i",    [0])

# Parameterized non-Clifford
sim2 = QuantumSimulator(2)
sim2.apply("rx",  [0], params=[math.pi/4])
sim2.apply("ry",  [1], params=[math.pi/3])
sim2.apply("rz",  [0], params=[math.pi/6])
sim2.apply("crz", [0, 1], params=[math.pi/2])
sim2.apply("rzz", [0, 1], params=[math.pi/4])
sim2.apply("ccx", [0, 1, 1])   # error: duplicate qubits
```

### 14.4 apply_gate() with Gate objects

```python
from stabilizer_python import HGate, TGate, CNOTGate, RZGate

sim = QuantumSimulator(2)
sim.apply_gate(HGate, [0])
sim.apply_gate(CNOTGate, [0, 1])
print(sim.mode)   # "tableau"

sim.apply_gate(TGate, [0])
print(sim.mode)   # "statevector"

sim.apply_gate(RZGate(math.pi/4), [1])
print(sim.sv.probabilities())
```

### 14.5 Measurement

```python
sim = QuantumSimulator(2)
sim.apply("h", [0]); sim.apply("cnot", [0, 1])

outcome_0 = sim.measure_z(0)
outcome_1 = sim.measure_z(1)
print(f"Outcomes: {outcome_0}, {outcome_1}")  # always match
```

### 14.6 reset()

```python
sim = QuantumSimulator(1)
sim.apply("h", [0])
sim.apply("t", [0])       # → statevector mode
sim.reset(0)               # measure + X correction → |0>
print(sim.sv.to_dict())    # {'0': (1+0j)}  approximately
```

### 14.7 statevector_snapshot()

```python
# Works in either mode — does not change mode
sim = QuantumSimulator(2)
sim.apply("h", [0]); sim.apply("cnot", [0, 1])
print(sim.mode)   # "tableau"

sv = sim.statevector_snapshot()   # converts tableau internally
print(sv.to_dict())   # {'00': 0.707, '11': 0.707}
print(sim.mode)       # still "tableau" — snapshot didn't switch it
```

### 14.8 debug=True — invariant checking

```python
sim = QuantumSimulator(3, debug=True)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("cnot", [0, 2])
# _check_tableau_invariants() called after every Clifford gate silently
print("Debug mode: invariants checked after each gate")
```

### 14.9 trace=True — gate-by-gate recording

```python
sim = QuantumSimulator(3, trace=True)
sim.apply("h", [0])
sim.apply("cnot", [0, 1])
sim.apply("t", [0])   # ← boundary: mode switches here

for step in sim.trace:
    print(f"Gate: {step.gate_name:8s}  "
          f"qubits: {step.qubits}  "
          f"{step.mode_before} → {step.mode_after}")
    if step.mode_after == "tableau":
        print("  ", step.snapshot.stabilizer_strings())
    else:
        print("  ", step.snapshot.to_dict())
```

### 14.10 Error cases

```python
sim = QuantumSimulator(3)

# Out-of-range qubit
try:
    sim.apply("h", [5])
except ValueError as e:
    print(e)

# Duplicate qubits on 2-qubit gate
try:
    sim.apply("cnot", [0, 0])
except ValueError as e:
    print(e)

# Unknown gate name
try:
    sim.apply("toffoli_modified", [0, 1, 2])
except ValueError as e:
    print(e)
```

---

## 15. Qiskit Interoperability

```python
# Requires: pip install qiskit
from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python.qiskit_interop import from_qiskit

# Pure Clifford circuit → stays in tableau mode
qc = QiskitCircuit(2)
qc.h(0)
qc.cx(0, 1)

sim = QuantumSimulator(2)
from_qiskit(qc).run(sim)
print(sim.mode)    # "tableau"
print(sim.tableau.stabilizer_strings())   # ['+XX', '+ZZ']

# Non-Clifford circuit → switches to statevector
qc2 = QiskitCircuit(2)
qc2.h(0)
qc2.t(0)
qc2.cx(0, 1)

sim2 = QuantumSimulator(2)
from_qiskit(qc2).run(sim2)
print(sim2.mode)    # "statevector"
print(sim2.sv.to_dict())

# With measurements
qc3 = QiskitCircuit(2, 2)
qc3.h(0); qc3.cx(0, 1); qc3.measure(0, 0); qc3.measure(1, 1)

sim3 = QuantumSimulator(2)
outcomes = from_qiskit(qc3).run(sim3)
print(outcomes)   # [0,0] or [1,1]

# Parameterized — bind first
import math
from qiskit.circuit import QuantumCircuit, Parameter
theta = Parameter("θ")
qc4 = QuantumCircuit(1)
qc4.rz(theta, 0)
bound = qc4.assign_parameters({theta: math.pi/4})

sim4 = QuantumSimulator(1)
from_qiskit(bound).run(sim4)

# Unbound parameter raises ValueError
try:
    from_qiskit(qc4).run(QuantumSimulator(1))
except ValueError as e:
    print(e)

# Qiskit library circuits
from qiskit.circuit.library import QFT
qc_qft = QFT(3).decompose()
sim5 = QuantumSimulator(3)
from_qiskit(qc_qft).run(sim5)
print(sim5.sv.probabilities())

# Supported gate name mapping
# cx → cnot,  measure → mz,  u1 → p,  u3/u → u
# barrier and delay are silently skipped
qc6 = QiskitCircuit(2)
qc6.cx(0, 1)      # → cnot
qc6.barrier()     # → skipped
from_qiskit(qc6)  # works cleanly
```

---

## 16. StabilizerDecomposition — T-gate Simulation

### 16.1 Basic usage

```python
# State as weighted sum of stabilizer states
d = StabilizerDecomposition(2)
print(d.term_count)   # 1  (starts as |00>)

d.h(0)
print(d.term_count)   # still 1 — H is Clifford

d.t(0)               # T gate splits: Z=+1 branch and Z=-1 branch
print(d.term_count)   # 2  (one term per eigenspace)
print(d.t_count)      # 1
```

### 16.2 T-gate depth grows term count

```python
d = StabilizerDecomposition(3)
d.h(0); d.h(1); d.h(2)

for _ in range(4):
    d.t(0)

print(f"After 4 T gates: {d.term_count} terms")   # up to 2^4 = 16 terms
print(d.summary())
```

### 16.3 All supported gates

```python
d = StabilizerDecomposition(4)

# Clifford gates — no term increase
d.h(0).s(1).sdg(2).sx(3).sxdg(0)
d.x(1).y(2).z(3).i(0)
d.cnot(0,1).cx(0,1).cz(1,2).cy(2,3).swap(0,3)

# Non-Clifford — doubles terms
d.t(0)     # → 2 terms
d.tdg(1)   # → 4 terms
```

### 16.4 Measurement on decomposition

```python
random.seed(0)
d = StabilizerDecomposition(2)
d.h(0).t(0).cnot(0, 1)

outcome = d.measure_z(0)
print(f"Outcome: {outcome}")
print(f"Terms after measurement: {d.term_count}")
```

### 16.5 Expectation values

```python
d = StabilizerDecomposition(1)
d.h(0)   # |+>

z_exp = d.expectation_z(0)
print(f"<Z> for |+> = {z_exp:.4f}")   # ≈ 0.0 (X eigenstate)

d2 = StabilizerDecomposition(1)
d2.h(0); d2.t(0)    # T|+> — not a stabilizer state

z_exp2 = d2.expectation_z(0)
print(f"<Z> for T|+> = {z_exp2:.4f}")   # 0.0 by symmetry
```

### 16.6 Inner product with |0>

```python
d = StabilizerDecomposition(1)
d.h(0)

amp = d.inner_product_with_zero()
print(f"|<0|+>|^2 = {abs(amp)**2:.4f}")   # ≈ 0.5

d2 = StabilizerDecomposition(1)
d2.h(0); d2.t(0)
amp2 = d2.inner_product_with_zero()
print(f"|<0|T|+>|^2 = {abs(amp2)**2:.4f}")
```

### 16.7 Unsupported gate raises NotImplementedError

```python
d = StabilizerDecomposition(1)
try:
    d.rz(0, math.pi/4)
except NotImplementedError as e:
    print(e)   # Use QuantumSimulator for arbitrary Rz
```

---

## 17. Mixed State — NoisyStabilizerState

### 17.1 Basic construction and gates

```python
n = NoisyStabilizerState(2)
print(n.ensemble_size)   # 1 — starts as pure state

n.h(0).cnot(0, 1)
print(n.ensemble_size)   # still 1 — Clifford preserves purity
```

### 17.2 Pauli noise branches into ensemble

```python
n = NoisyStabilizerState(2)
n.h(0).cnot(0, 1)

n.apply_pauli_channel(0, p_x=0.1, p_y=0.05, p_z=0.1)
print(n.ensemble_size)   # 4: I, X, Y, Z branches
for ws in n.ensemble:
    print(f"  p={ws.probability:.3f}  stabs={ws.state.stabilizer_strings()}")
```

### 17.3 Noise channel helpers

```python
n = NoisyStabilizerState(2)
n.apply_depolarising(0, p=0.01)
n.apply_bit_flip(1, p=0.05)
n.apply_phase_flip(0, p=0.02)
print(n.ensemble_size)
```

### 17.4 Measurement collapses ensemble

```python
random.seed(5)
n = NoisyStabilizerState(2)
n.h(0).cnot(0, 1)
n.apply_depolarising(0, p=0.01)

outcome = n.measure_z(0)
print(f"Outcome: {outcome}")
print(f"Ensemble size after: {n.ensemble_size}")

# Prune near-zero terms
n.prune(threshold=1e-6)
print(f"After prune: {n.ensemble_size}")
```

### 17.5 Summary and dominant state

```python
n = NoisyStabilizerState(2)
n.h(0); n.apply_depolarising(0, p=0.1)

print(n.summary())
print(f"Dominant probability: {n.dominant_probability():.3f}")
dominant = n.dominant_state()
print(dominant.stabilizer_strings())
```

### 17.6 PauliChannel

```python
# Named constructors
depol  = PauliChannel.depolarising(p=0.01)
bitflip = PauliChannel.bit_flip(p=0.05)
phflip  = PauliChannel.phase_flip(p=0.02)
bpflip  = PauliChannel.bit_phase_flip(p=0.01)
custom  = PauliChannel(p_x=0.01, p_y=0.005, p_z=0.01, name="custom")

n = NoisyStabilizerState(3)
depol.apply(n, qubit=0)
bitflip.apply(n, qubit=1)
depol.apply_all(n)    # apply to every qubit
print(n.summary())
```

### 17.7 Magic state metrics

```python
# Magic state T|+>
d = StabilizerDecomposition(1)
d.h(0); d.t(0)

extent  = stabilizer_extent(d)
entropy = stabilizer_entropy(d)
fidelity = stabilizer_fidelity(d)

print(f"Stabilizer extent:  {extent:.4f}")    # > 1 for magic states
print(f"Stabilizer entropy: {entropy:.4f}")   # > 0 for magic states
print(f"Stabilizer fidelity:{fidelity:.4f}")  # < 1 for magic states

# Clifford state should be exactly stabilizable
d2 = StabilizerDecomposition(1)
d2.h(0)   # |+> — a stabilizer state
e2 = stabilizer_extent(d2)
print(f"Extent of |+>: {e2:.4f}")   # 1.0
```

---

## 18. Step-by-Step Tracing

### 18.1 TracedCircuit basics

```python
from stabilizer_python.codes import BitFlip3Code as LegacyBitFlip

# Encode with an error, then trace syndrome extraction
st = StabilizerState.zero(5)
LegacyBitFlip.encoder_circuit().run(st)
st.x(1)   # X error on qubit 1

tc = TracedCircuit(LegacyBitFlip.syndrome_circuit(), trace=True)
outcomes = tc.run(st)
print(f"Syndrome outcomes: {outcomes}")   # [1, 1] → error on qubit 1
```

### 18.2 Examining trace steps

```python
for step in tc.steps:
    print(f"\nStep {step.index}: {step.op_label}  ({step.kind})")
    if step.kind == "measurement":
        print(f"  outcome={step.outcome}  branch={step.measurement_branch}")
    print(step.state.format_chp_printstate())
```

### 18.3 print_trace()

```python
tc.print_trace()
# Prints each step with operation, outcome info, and tableau
```

### 18.4 trace=False for production

```python
tc_fast = TracedCircuit(LegacyBitFlip.syndrome_circuit(), trace=False)
st = StabilizerState.zero(5)
LegacyBitFlip.encoder_circuit().run(st)

outcomes = tc_fast.run(st)
print(f"Outcomes: {outcomes}")
print(f"Steps recorded: {len(tc_fast.steps)}")   # 0
```

### 18.5 TraceStep fields

```python
step = tc.steps[0]
print(step.index)              # 1
print(step.op_label)           # e.g. "CNOT(0, 3)"
print(step.kind)               # "gate" or "measurement"
print(step.state.n)            # n of the tableau at that moment
print(step.outcome)            # None for gates, 0/1 for measurements
print(step.measurement_branch) # None for gates, "deterministic"/"random"
```

### 18.6 Non-Clifford raises in TracedCircuit

```python
tc_bad = TracedCircuit(Circuit(1).t(0), trace=True)
try:
    tc_bad.run(StabilizerState.zero(1))
except ValueError as e:
    print(e)   # "TracedCircuit tracing requires Clifford operations in tableau mode"
```

---

## 19. Ancilla Register & Parity Checks

### 19.1 Direct parity check functions

```python
from stabilizer_python import x_parity_check, z_parity_check, mixed_parity_check

state = StabilizerState.zero(3)
state.x(1)   # bit-flip on qubit 1

# Add ancilla
state.add_ancilla_zero()
ancilla = 3

# Z-parity check on qubits 0,1
result = z_parity_check(state, ancilla=ancilla, data_qubits=[0, 1])
print(f"Z-parity q0,q1 = {result}")   # 1 (X on qubit 1 → odd parity)
state.remove_ancilla(ancilla)

# X-parity check
state2 = StabilizerState.zero(3)
for q in range(3):
    state2.h(q)   # all |+>
state2.add_ancilla_zero()
result2 = x_parity_check(state2, ancilla=3, data_qubits=[0, 1, 2])
print(f"X-parity = {result2}")   # 0

# Mixed parity check (arbitrary Pauli)
state3 = SteaneCode.zero_state()
state3.add_ancilla_zero()
result3 = mixed_parity_check(
    state3, ancilla=7,
    data_qubits=[0,1,2,3,4,5,6],
    pauli_types=list("IIIXXXX")
)
print(f"IIIXXXX check = {result3}")   # 0 on clean codeword
state3.remove_ancilla(7)
```

### 19.2 AncillaRegister

```python
state = SteaneCode.zero_state()
reg = AncillaRegister(state, names=["s1", "s2", "s3"])

print(f"n with ancillas: {state.n}")   # 10 (7 + 3)
print(f"n ancillas: {reg.n_ancillas()}")   # 3
print(f"ancilla indices: {reg.ancilla_indices}")

# Use ancillas for parity checks
data = list(range(7))
r1 = reg.z_parity(  "s1", [0, 1, 2])
r2 = reg.x_parity(  "s2", [3, 4, 5])
r3 = reg.mixed_parity("s3", data, list("IIIXXXX"))
print(f"Checks: {r1}, {r2}, {r3}")

# Duplicate ancilla names raise ValueError
try:
    AncillaRegister(StabilizerState.zero(3), names=["a", "a"])
except ValueError as e:
    print(e)
```

---

## 20. GF(2) Linear Algebra

### 20.1 gaussian_elimination_gf2

```python
M = [
    [1, 0, 1, 1],
    [0, 1, 1, 0],
    [1, 1, 0, 1],
]

rref, pivots = gaussian_elimination_gf2(M)
print("RREF:")
for row in rref:
    print(" ", row)
print("Pivot columns:", pivots)   # [0, 1, 2]
```

### 20.2 rank_gf2

```python
# Full rank
M_full = [[1,0,0],[0,1,0],[0,0,1]]
print(rank_gf2(M_full))   # 3

# Rank-deficient (last row = sum of first two)
M_dep = [[1,1,0],[0,1,1],[1,0,1]]
print(rank_gf2(M_dep))    # 2

# Verify generator independence with rank
generators = ["+ZZI", "+IZZ"]
# Build check matrix [X|Z] for each generator
rows = []
for g in generators:
    phase, x, z = 0, [], []
    for ch in g.lstrip("+-"):
        x.append(1 if ch in "XY" else 0)
        z.append(1 if ch in "YZ" else 0)
    rows.append(x + z)

r = rank_gf2(rows)
n, k = 3, 1
print(f"rank={r}, expected={n-k}, independent={r == n-k}")   # True

# Validation
try:
    rank_gf2([[1,0],[1]])   # unequal row lengths
except ValueError as e:
    print(e)
```

---

## 21. Gate Objects

### 21.1 Gate dataclass fields

```python
print(f"name:       {HGate.name}")        # 'h'
print(f"num_qubits: {HGate.num_qubits}")  # 1
print(f"is_clifford:{HGate.is_clifford}") # True
print(f"params:     {HGate.params}")      # []
print(f"matrix shape: {HGate.matrix.shape}")  # (2, 2)

print(TGate.is_clifford)    # False
print(CNOTGate.num_qubits)  # 2
```

### 21.2 Fixed single-qubit gates

```python
from stabilizer_python import (
    IGate, HGate, XGate, YGate, ZGate,
    SGate, SdgGate, SXGate, SXdgGate,
    TGate, TdgGate,
)

for g in [IGate, HGate, XGate, YGate, ZGate, SGate, SdgGate, SXGate, SXdgGate]:
    print(f"{g.name:8s}  Clifford={g.is_clifford}")

for g in [TGate, TdgGate]:
    print(f"{g.name:8s}  Clifford={g.is_clifford}")   # False
```

### 21.3 Fixed two-qubit gates

```python
from stabilizer_python import (
    CXGate, CNOTGate, CYGate, CZGate, CHGate,
    SwapGate, iSwapGate, ECRGate, DCXGate, CSGate, CSdgGate,
)
for g in [CXGate, CNOTGate, CYGate, CZGate, CHGate, SwapGate, iSwapGate]:
    print(f"{g.name:8s}  Clifford={g.is_clifford}  n={g.num_qubits}")
```

### 21.4 Fixed three-qubit gates

```python
from stabilizer_python import CCXGate, ToffoliGate, CCZGate, CSwapGate, FredkinGate, MCXGate
for g in [CCXGate, ToffoliGate, CCZGate, CSwapGate, FredkinGate, MCXGate]:
    print(f"{g.name:10s}  Clifford={g.is_clifford}  n={g.num_qubits}")
```

### 21.5 Parameterized gate factories

```python
from stabilizer_python import (
    RXGate, RYGate, RZGate, PhaseGate, U1Gate, U2Gate, U3Gate, UGate, RGate,
    CRXGate, CRYGate, CRZGate, CPhaseGate,
    RXXGate, RYYGate, RZZGate, RZXGate,
    XXPlusYYGate, XXMinusYYGate,
)

g_rx = RXGate(math.pi/4)
print(f"name={g_rx.name}  params={g_rx.params}  Clifford={g_rx.is_clifford}")

g_crz = CRZGate(math.pi/3)
print(f"name={g_crz.name}  n={g_crz.num_qubits}")

g_rxx = RXXGate(math.pi/4)
print(f"name={g_rxx.name}  matrix shape={g_rxx.matrix.shape}")
```

### 21.6 Gate matrices

```python
import numpy as np

print("H matrix:")
print(np.round(HGate.matrix, 4))

print("\nT matrix (diagonal):")
print(np.round(np.diag(TGate.matrix), 4))

print("\nCNOT matrix:")
print(CNOTGate.matrix.real.astype(int))
```

---

## 22. Statevector Backend

### 22.1 Statevector class

```python
# Default: |0...0>
sv = Statevector(3)
print(sv.n)             # 3
print(sv.data[:4])      # [1+0j, 0, 0, 0, ...]

# From data
import numpy as np
data = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
sv2 = Statevector(2, data)
print(sv2.to_dict())    # {'00': 0.707..., '11': 0.707...}
```

### 22.2 apply_gate and measure_z

```python
from stabilizer_python import HGate, CNOTGate

sv = Statevector(2)
sv.apply_gate(HGate, [0])
sv.apply_gate(CNOTGate, [0, 1])

print(sv.probabilities())   # [0.5, 0, 0, 0.5]
print(sv.to_dict())         # {'00': 0.707, '11': 0.707}

outcome = sv.measure_z(0)
print(f"Outcome: {outcome}")
print(sv.probabilities())   # collapsed to one state
```

### 22.3 inner_product

```python
sv1 = Statevector(1)   # |0>
sv2 = Statevector(1)
sv2.apply_gate(HGate, [0])   # |+>

ip = sv1.inner_product(sv2)
print(f"<0|+> = {ip:.4f}")        # 0.7071+0j
print(f"|<0|+>|^2 = {abs(ip)**2:.4f}")   # 0.5
```

### 22.4 tableau_to_statevector

```python
# Convert a stabilizer tableau to a dense statevector
st = StabilizerState.zero(2)
st.h(0); st.cnot(0, 1)   # Bell state

sv = tableau_to_statevector(st)
print(sv.to_dict())   # {'00': 0.707..., '11': 0.707...}

# Works on any stabilizer state
ghz_st = StabilizerState.zero(3)
ghz_st.h(0)
for q in range(1, 3):
    ghz_st.cnot(0, q)

sv_ghz = tableau_to_statevector(ghz_st)
print(sv_ghz.to_dict())   # {'000': 0.707, '111': 0.707}
```

---

## 23. Legacy codes.py Helpers

```python
from stabilizer_python import codes
from stabilizer_python.codes import BitFlip3Code as L_BF, Shor9Code as L_S9

# encoder_circuit()
c = L_BF.encoder_circuit()
print(c.n_qubits)   # 3
st = StabilizerState.zero(3)
c.run(st)
print(st.stabilizer_strings())   # ['+ZZI', '+IZZ']

# syndrome_circuit() — 5 qubits (3 data + 2 ancilla)
sc = L_BF.syndrome_circuit()
st5 = StabilizerState.zero(5)
L_BF.encoder_circuit().run(st5)
st5.x(1)   # error on qubit 1
outcomes = sc.run(st5)
print(f"Syndrome from circuit: {outcomes}")   # [1, 1]

# measure_syndrome() — ancilla-based, resets ancilla
st_new = StabilizerState.zero(5)
L_BF.encoder_circuit().run(st_new)
st_new.x(2)
s01, s12 = L_BF.measure_syndrome(st_new)
print(f"Syndrome: ({s01}, {s12})")   # (0, 1)

# correct_x_from_syndrome()
L_BF.correct_x_from_syndrome(st_new, s01, s12)
s01_after, s12_after = L_BF.measure_syndrome(st_new)
print(f"After correction: ({s01_after}, {s12_after})")  # (0, 0)

# read_syndrome() — reads from phase bits directly, no ancilla
st3 = StabilizerState.zero(3)
L_BF.encoder_circuit().run(st3)
st3.x(0)
print(L_BF.read_syndrome(st3))   # (1, 0)

# Shor 9-qubit
st9 = StabilizerState.zero(9)
L_S9.encoder_circuit().run(st9)
st9.x(4)                                    # error on qubit 4
syn9 = L_S9.read_syndrome(st9)
print(f"Shor syndrome: {syn9}")
L_S9.correct_x_from_syndrome(st9, syn9)
print(f"After correction: {L_S9.read_syndrome(st9)}")  # all zeros

# Convenience helpers
bell_st, _ = codes.run_2qubit_bell()
print(bell_st.stabilizer_strings())   # ['+XX', '+ZZ']

enc_zero = codes.bitflip3_encode_zero_state()
print(enc_zero.stabilizer_strings())  # ['+ZZI', '+IZZ']
```

---

## 24. Scale Demonstration

### 24.1 Large GHZ — showing O(n²) beats O(2^n)

```python
import time

# 500-qubit GHZ — completely impossible with statevector (2^500 amplitudes)
n = 500
t0 = time.perf_counter()
st = StabilizerState.zero(n)
st.h(0)
for q in range(1, n):
    st.cnot(0, q)
t1 = time.perf_counter()

print(f"Prepared {n}-qubit GHZ in {t1-t0:.3f}s")
print(f"Tableau size: {2*n} x {2*n+1} = {2*n*(2*n+1)} bits ≈ {2*n*(2*n+1)//8192} KB")

# All measurements must be 0 or all 1 — verify
outcomes = [st.measure_z(0)]   # first qubit
# After first measurement, rest are deterministic
outcomes += [st.measure_z(q) for q in range(1, min(n, 10))]
print(f"First 10 outcomes: {outcomes}")
assert len(set(outcomes)) == 1, "GHZ correlation violated"
print("GHZ correlations hold across all qubits ✓")
```

### 24.2 Deep random Clifford circuit

```python
import random as rng

rng.seed(42)
n = 200
depth = 500

t0 = time.perf_counter()
st = StabilizerState.zero(n)
gates_applied = 0

for _ in range(depth):
    gate_type = rng.choice(["h", "s", "cnot"])
    if gate_type == "h":
        st.h(rng.randint(0, n-1))
    elif gate_type == "s":
        st.s(rng.randint(0, n-1))
    else:
        a = rng.randint(0, n-1)
        b = rng.randint(0, n-2)
        if b >= a:
            b += 1
        st.cnot(a, b)
    gates_applied += 1

t1 = time.perf_counter()
total_ms = (t1 - t0) * 1000
print(f"{gates_applied} random Clifford gates on {n} qubits")
print(f"Total time: {total_ms:.1f} ms  ({total_ms/gates_applied:.3f} ms/gate)")
```

### 24.3 QEC at scale — many correction rounds

```python
rng.seed(0)
n_shots = 1000
n_errors = 0

for shot in range(n_shots):
    state = BitFlip3Code.zero_state()
    # Random single-qubit X error with p=0.05
    if rng.random() < 0.05:
        q = rng.randint(0, 2)
        state.x(q)
    syndrome = BitFlip3Code.read_syndrome(state)
    # Decode
    correction_table = {
        (0,0): None,
        (1,0): 0,
        (1,1): 1,
        (0,1): 2,
    }
    q_fix = correction_table.get(tuple(syndrome))
    if q_fix is not None:
        state.x(q_fix)
    # Check logical state is recovered
    syndrome_after = BitFlip3Code.read_syndrome(state)
    if any(syndrome_after):
        n_errors += 1

print(f"Logical error rate after correction: {n_errors/n_shots:.4f}")
print(f"(physical error rate was 0.05, code corrects 1 error)")
```

---

## Quick Reference — All Public Exports

```
StabilizerState       Core Clifford simulator (tableau)
Circuit               Fluent gate builder
QuantumSimulator      Hybrid Clifford+statevector router
StabilizerCode        General [[n,k,d]] code class
EncodedState          Logical operator tracking
SyndromeExtractor     Reusable syndrome extraction
read_syndrome()       One-shot syndrome function

BitFlip3Code          Named code instances
PhaseFlip3Code
PerfectCode
SteaneCode
Shor9Code
SurfaceCode3

apply_pauli_channel   Single-qubit noise
apply_depolarizing
apply_bit_flip
apply_phase_flip
apply_bit_phase_flip
apply_*_all()         Multi-qubit noise variants
NoisyCircuit          Circuit-level noise injection
run_shots()           Low-level Monte Carlo loop

benchmark_code()      Shot-based decoder evaluation
threshold_scan()      Sweep physical error rates
compare_codes()       Multi-code comparison
build_lookup_decoder()Enumerate syndrome→correction table

StabilizerDecomposition   T-gate via stabilizer rank
NoisyStabilizerState      Classical mixture of stabilizer states
PauliChannel              Named noise channel object
stabilizer_fidelity()     Magic state metric
stabilizer_extent()       Robustness measure
stabilizer_entropy()      Rényi entropy over decomposition

AncillaRegister        Named ancilla pool
x_parity_check()       Pauli parity helpers
z_parity_check()
y_parity_check()
mixed_parity_check()

gaussian_elimination_gf2()  GF(2) RREF
rank_gf2()                  Binary rank

Statevector               Dense non-Clifford backend
tableau_to_statevector()  Convert tableau to dense vector

Gate                  Dataclass: name, matrix, is_clifford, params
HGate XGate YGate ZGate SGate SdgGate SXGate SXdgGate  — fixed Clifford
TGate TdgGate                                            — fixed non-Clifford
CXGate CNOTGate CYGate CZGate CHGate SwapGate iSwapGate — 2-qubit Clifford
CCXGate CCZGate CSwapGate ToffoliGate MCXGate            — 3-qubit
RXGate() RYGate() RZGate() PhaseGate() UGate()           — parameterized 1-qubit
CRXGate() CRYGate() CRZGate() CPhaseGate()               — parameterized 2-qubit
RXXGate() RYYGate() RZZGate() RZXGate()                  — 2-qubit rotations

TracedCircuit         Step-by-step tableau recording
from_qiskit()         Convert Qiskit QuantumCircuit
codes.BitFlip3Code    Legacy explicit-circuit helpers
codes.Shor9Code
codes.run_2qubit_bell()
```