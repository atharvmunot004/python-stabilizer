import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qiskit import QuantumCircuit as QiskitCircuit
from stabilizer_python import QuantumSimulator
from stabilizer_python.qiskit_interop import from_qiskit

qc = QiskitCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)

sim = QuantumSimulator(3)
from_qiskit(qc).run(sim)

print("Mode:", sim.mode)  # "tableau" — pure Clifford circuit

# Access the tableau and print the CHP-style tableau directly.
print(sim.tableau.format_chp_printstate())

# Unified tableau inspection API.
#
# Default: prints the compact CHP-style view only.
print("\ninspect() default: chp view")
print(sim.tableau.inspect())

# Request all main views explicitly, separated by blank lines:
# - chp: CHP-style destabilizer/stabilizer rows
# - binary: raw X and Z bit matrices
# - phase: phase-bit column
# - debug: CHP rows plus binary and phase matrices
print("\ninspect(['chp', 'binary', 'phase', 'debug']):")
print(sim.tableau.inspect(views=["chp", "binary", "phase", "debug"]))

# Selective output: pass the exact view names you want.
print("\ninspect(['chp']):")
print(sim.tableau.inspect(views=["chp"]))

print("\ninspect(['binary']):")
print(sim.tableau.inspect(views=["binary"]))

print("\ninspect(['phase']):")
print(sim.tableau.inspect(views=["phase"]))

print("\ninspect(['debug']):")
print(sim.tableau.inspect(views=["debug"]))

print("\ninspect(['stabilizers']):")
print(sim.tableau.inspect(views=["stabilizers"]))

print("\ninspect(['destabilizers']):")
print(sim.tableau.inspect(views=["destabilizers"]))

print("\ninspect(['chp', 'binary', 'phase']):")
print(sim.tableau.inspect(views=["chp", "binary", "phase"]))

print("\nstabilizer_strings():")
print(sim.tableau.stabilizer_strings())

print("\ndestabilizer_strings():")
print(sim.tableau.destabilizer_strings())

# Also print just the stabilizer generators with their Pauli strings
print("\nStabilizer generators:")
for phase, x_row, z_row in sim.tableau.stabilizer_generators():
    sign = "-" if phase else "+"
    pauli = ""
    for q in range(sim.n):
        xb, zb = x_row[q], z_row[q]
        if xb == 0 and zb == 0:
            pauli += "I"
        elif xb == 1 and zb == 0:
            pauli += "X"
        elif xb == 1 and zb == 1:
            pauli += "Y"
        else:
            pauli += "Z"
    print(f"  {sign}{pauli}")