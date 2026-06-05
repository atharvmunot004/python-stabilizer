# Running Tests

Clone the repository and install development dependencies:

```bash
git clone https://github.com/atharvmunot004/python-stabilizer.git
cd python-stabilizer
pip install -e ".[dev]"
pytest
```

The test suite covers individual gates, Bell/GHZ states, bit-flip code behavior, Shor-code encoding and correction helpers, GF(2) linear algebra, random Clifford circuits, random measurements, Qiskit interoperability, non-Clifford hybrid simulation, tableau inspection, and traced circuit output.

## Useful Test Entry Points

| Test file | Purpose |
|---|---|
| [`tests/test_two_qubit_bell.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_two_qubit_bell.py) | Bell-state preparation and stabilizers |
| [`tests/test_bitflip3.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_bitflip3.py) | 3-qubit repetition-code syndrome and correction |
| [`tests/test_random_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_random_circuits.py) | Tableau invariants under random Clifford and measurement circuits |
| [`tests/test_qiskit_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_qiskit_circuits.py) | Small Qiskit-to-local circuit comparisons |
| [`tests/test_nonclifford_gates.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_nonclifford_gates.py) | Hybrid statevector fallback and non-Clifford gates |
| [`tests/test_inspect.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_inspect.py) | `StabilizerState.inspect()` default and selective views |
| [`tests/test_traced_circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_traced_circuit.py) | Step-by-step traced syndrome circuits |

## Docs-Style Example Script

`tests/test-from-docs.py` is a runnable script-style example. It shows:

- Qiskit conversion through `from_qiskit()`
- `QuantumSimulator` staying in tableau mode for a pure Clifford circuit
- direct CHP-style tableau output
- `inspect()` default output
- every selective `inspect()` view
- manual iteration over `stabilizer_generators()`

Run it as a file path, not with `python -m`:

```bash
python tests/test-from-docs.py
```

On Windows PowerShell:

```powershell
python "tests/test-from-docs.py"
```

Do not run it as `python -m .\tests\test-from-docs.py`; `-m` expects a module name, not a file path.

## CI

The GitHub Actions workflow runs:

```bash
pip install -e ".[dev]"
pytest -q
```

on Python 3.9, 3.11, and 3.12.
