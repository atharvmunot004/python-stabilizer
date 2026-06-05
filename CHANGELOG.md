# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers
use [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-05

### Added

- **`QuantumSimulator`**: hybrid simulator that runs Clifford gates on the
  Aaronson–Gottesman tableau and switches to a dense statevector backend at
  the first non-Clifford gate.
- **`Statevector` backend** and `tableau_to_statevector()` bridge for
  non-Clifford simulation and state inspection.
- **`Gate` hierarchy**: typed gate objects covering Clifford gates, `T`/`Tdg`,
  single-qubit rotations, Toffoli/CCX, and the Qiskit-standard gate set.
- **Qiskit interop**: `from_qiskit()` converts a Qiskit `QuantumCircuit` into
  a local `Circuit` for use with `StabilizerState` or `QuantumSimulator`.
- **Extended `Circuit` builder**: non-Clifford gate methods and support for
  running on either `StabilizerState` or `QuantumSimulator`.
- **Additional Clifford gates** on `StabilizerState`: `Sdg`, `SX`, `CY`, `CZ`,
  `SWAP`, and related helpers.
- **MkDocs documentation** under `docs/` (theory, API reference, hybrid
  simulation guide, getting started).
- **GitHub Actions CI** (`.github/workflows/ci.yml`) testing Python 3.9, 3.11,
  and 3.12.
- **Proof notes** for the X-gate tableau update in `docs/proofs/`.

### Changed

- README install URL now points to `python-stabilizer` (the standalone repo).
- README "What you get" section updated for hybrid simulation and Qiskit
  interop.
- X-gate proof notes moved from the repo root to `docs/proofs/` and linked from
  the tableau theory page.

### Removed

- `site/` MkDocs build output and `pytest_out.txt` from version control
  (regenerate locally with `mkdocs build`).

## [0.1.0] - 2026-05-29

Initial release.

### Added

- **`StabilizerState`**: Aaronson–Gottesman tableau simulator for Clifford
  gates and Z-basis measurement.
- **`Circuit`**: fluent builder for small Clifford circuits.
- **QEC examples**: 3-qubit bit-flip code and 9-qubit Shor code encoders with
  syndrome extraction helpers.
- **GF(2) utilities**: `gaussian_elimination_gf2` and `rank_gf2`.
- Runnable examples and pytest test suite for tableau invariants and QEC demos.
