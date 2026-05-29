# stabilizer-python Repository Structure

This document describes the layout of `stabilizer-python/`, a minimal pure-Python stabilizer/Clifford simulator with small error-correcting-code examples.

Generated Python cache files such as `__pycache__/` and `*.pyc` are runtime artifacts and are not part of the source layout.

## Directory Tree

```text
stabilizer-python/
├── README.md
├── REPO_STRUCTURE.md
├── pyproject.toml
├── pytest_out.txt
├── x-gate-proof.md
├── x-gate-proof.pdf
├── references/
│   ├── Gottesman-Knill Theorem-part 1.ipynb
│   ├── Gottesman-knill Theorem Part-2.ipynb
│   ├── Stabilizer Formalism.pdf
│   ├── Stabilizers codes.pdf
│   └── stabilizer.pdf
├── stabilizer_python/
│   ├── __init__.py
│   ├── circuit.py
│   ├── codes.py
│   ├── linear_algebra.py
│   ├── tableau.py
│   └── examples/
│       ├── __init__.py
│       ├── bitflip3_demo.py
│       ├── shor9_demo.py
│       └── two_qubit_bell.py
└── tests/
    ├── conftest.py
    ├── test_additional_clifford_gates.py
    ├── test_bitflip3.py
    ├── test_gaussian_elimination.py
    ├── test_qiskit_circuits.py
    ├── test_random_circuits.py
    └── test_two_qubit_bell.py
```

## Top-Level Files

| Path | Description |
| --- | --- |
| `README.md` | Main project overview, installation commands, example commands, and test instructions. |
| `REPO_STRUCTURE.md` | This repository map. |
| `pyproject.toml` | Python packaging metadata for `stabilizer-python`, setuptools package discovery, dev dependencies, and pytest options. |
| `pytest_out.txt` | Captured pytest output from a previous run. This is an artifact, not library source. |
| `x-gate-proof.md` | Markdown notes explaining X-gate behavior in the stabilizer formalism. |
| `x-gate-proof.pdf` | PDF version of the X-gate proof notes. |

## `stabilizer_python/`

This is the installable Python package. It contains the simulator core, circuit helper API, finite-field linear algebra utilities, and error-correcting-code helpers.

| Path | Description |
| --- | --- |
| `stabilizer_python/__init__.py` | Public package exports: `StabilizerState`, `Circuit`, `gaussian_elimination_gf2`, `rank_gf2`, and `codes`. |
| `stabilizer_python/tableau.py` | Core Aaronson-Gottesman-style stabilizer tableau implementation. Defines `StabilizerState`, zero-state construction, tableau copying, Clifford gates, Pauli gates, controlled gates, measurement, reset, stabilizer extraction, and debug formatting. |
| `stabilizer_python/circuit.py` | Lightweight circuit builder. Defines the `Op` dataclass and fluent `Circuit` API for appending gates and measurements, then running them on a `StabilizerState`. |
| `stabilizer_python/linear_algebra.py` | Binary matrix helpers over GF(2), including reduced row-echelon form via `gaussian_elimination_gf2` and matrix rank via `rank_gf2`. |
| `stabilizer_python/codes.py` | Error-correcting-code helpers. Includes `BitFlip3Code` for the 3-qubit repetition code, `Shor9Code` for a 9-qubit Shor-code encoder and X-error correction helpers, plus small convenience routines. |

## `stabilizer_python/examples/`

Runnable example modules. These can be launched with `python -m stabilizer_python.examples.<module>` after installing the package.

| Path | Description |
| --- | --- |
| `stabilizer_python/examples/__init__.py` | Marks the examples directory as a Python package. |
| `stabilizer_python/examples/two_qubit_bell.py` | Builds a two-qubit Bell state and prints the resulting stabilizer tableau. |
| `stabilizer_python/examples/bitflip3_demo.py` | Demonstrates the 3-qubit bit-flip code: encode, inject an X error, measure syndrome, and correct. |
| `stabilizer_python/examples/shor9_demo.py` | Demonstrates the Shor 9-qubit code encoder, an injected X error, syndrome extraction, and correction. |

## `tests/`

Pytest suite for the simulator, algebra helpers, code examples, random Clifford behavior, and optional Qiskit interoperability.

| Path | Description |
| --- | --- |
| `tests/conftest.py` | Adds the repository root to `sys.path` so tests can import `stabilizer_python` reliably. |
| `tests/test_two_qubit_bell.py` | Checks that the Bell-state example has the expected `+ZZ` and `+XX` stabilizer behavior. |
| `tests/test_additional_clifford_gates.py` | Verifies extended Clifford and Pauli gate implementations against equivalent decompositions, including identity, Y, S dagger, square-root X, CX, CZ, CY, and SWAP. |
| `tests/test_gaussian_elimination.py` | Tests GF(2) Gaussian elimination, rank calculation, input immutability, and validation for empty, ragged, and non-binary matrices. |
| `tests/test_bitflip3.py` | Tests the 3-qubit bit-flip code syndrome table, confirms Z errors are invisible to the Z-parity syndrome, and checks correction of single X errors. |
| `tests/test_random_circuits.py` | Runs randomized Clifford-circuit checks for inverse round trips, valid stabilizer generators, and measurement-preserved tableau validity. |
| `tests/test_qiskit_circuits.py` | Converts supported Qiskit Clifford circuits into the local `Circuit` API and checks stabilizers for Bell, GHZ, and Bell-plus-Z circuits. Requires the `qiskit` dev dependency. |

## `references/`

Background material for the stabilizer formalism and Gottesman-Knill theorem.

| Path | Description |
| --- | --- |
| `references/stabilizer.pdf` | Reference PDF about stabilizer states or stabilizer simulation. |
| `references/Stabilizer Formalism.pdf` | Reference PDF focused on the stabilizer formalism. |
| `references/Stabilizers codes.pdf` | Reference PDF about stabilizer codes. |
| `references/Gottesman-Knill Theorem-part 1.ipynb` | Notebook material for the first part of the Gottesman-Knill theorem notes. |
| `references/Gottesman-knill Theorem Part-2.ipynb` | Notebook material for the second part of the Gottesman-Knill theorem notes. |

## How The Pieces Fit Together

`StabilizerState` in `tableau.py` is the core state representation. `Circuit` in `circuit.py` records simple gate operations and applies them to a `StabilizerState`. `codes.py` builds on both modules to define small quantum error-correcting-code workflows. `linear_algebra.py` supports tests and validation logic that need GF(2) rank or row reduction.

The examples show typical usage from the command line, while the tests validate individual gates, circuit behavior, error-correction routines, random Clifford circuits, and compatibility with supported Qiskit circuit operations.

