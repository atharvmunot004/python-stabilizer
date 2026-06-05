# stabilizer-python

![CI](https://github.com/atharvmunot004/python-stabilizer/actions/workflows/ci.yml/badge.svg)

Minimal stabilizer (Clifford) simulator in pure Python, with a hybrid backend for non-Clifford gates and example error-correcting codes inspired by the CHP material.

### What you get

- **Stabilizer simulator**: tableau-based Aaronson–Gottesman style state update for Clifford gates and Z measurement.
- **Hybrid simulator (`QuantumSimulator`)**: runs Clifford circuits on the fast tableau backend and switches to a statevector backend at the first non-Clifford gate.
- **Non-Clifford gates**: `T`, rotations (`RX`/`RY`/`RZ`), Toffoli, and the full Qiskit gate set via typed `Gate` objects.
- **Qiskit interop**: load existing `QuantumCircuit` objects with `from_qiskit` and run them on `StabilizerState` or `QuantumSimulator`.
- **2-qubit circuits**: build and run small circuits (H, S, X, Z, CNOT, measurements, and more) through the fluent `Circuit` builder.
- **3-qubit bit-flip code**: encoder and Z-parity syndrome extraction (measures \(Z_0 Z_1\) and \(Z_1 Z_2\)).
- **9-qubit Shor code**: encoder built as phase-protection + three bit-flip blocks.

### Quick start

Install directly from GitHub:

```bash
python -m pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

For local development, install the package in editable mode:

```bash
cd python-stabilizer
python -m pip install -e ".[dev]"
```

Then run examples:

```bash
python -m stabilizer_python.examples.two_qubit_bell
python -m stabilizer_python.examples.bitflip3_demo
python -m stabilizer_python.examples.shor9_demo
```

Run tests:

```bash
pytest -q
```
