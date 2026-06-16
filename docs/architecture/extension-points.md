# Extension Points

This page explains where to extend the project and which tests/docs should move
with each type of change.

---

## Add A New Clifford Gate

Touch points:

1. Add a tableau update method to `StabilizerState` in `tableau.py`.
2. Add or reuse a `Gate` object in `gate.py` with `is_clifford=True`.
3. Add routing in `QuantumSimulator.apply_gate(...)` if the simulator does not
   already dispatch the gate.
4. Add a `Circuit` convenience method if the gate should be fluent.
5. Add Qiskit interop mapping if Qiskit has the same instruction.
6. Add proof or rule documentation under `docs/theory/`.
7. Add tests that compare the new gate to a decomposition or known stabilizers.

Do not set `is_clifford=True` unless the gate maps every Pauli to a Pauli under
conjugation.

---

## Add A New Non-Clifford Gate

Touch points:

1. Add a `Gate` instance or factory in `gate.py`.
2. Set `is_clifford=False`.
3. Add a `Circuit` convenience method if needed.
4. Ensure `QuantumSimulator` can construct or accept the gate.
5. Add statevector tests for amplitudes or probabilities.

Non-Clifford gates automatically switch `QuantumSimulator` from tableau mode to
statevector mode.

---

## Add A New Stabilizer Code

Preferred path:

```python
from stabilizer_python import StabilizerCode

MyCode = StabilizerCode(
    n=...,
    k=...,
    generators=[...],
    name="My Code [[n,k,d]]",
    logical_xs=[...],
    logical_zs=[...],
)
```

Checklist:

- generators have exactly `n-k` entries
- every generator has length `n`
- all generators commute
- generator matrix rank is `n-k`
- logical X/Z commute with stabilizers
- logical X/Z anticommute pairwise for each logical qubit
- `zero_state()` has all-zero syndrome
- known single-qubit errors produce nonzero syndromes when the code should detect them
- `distance()` matches the expected value for small codes

Add public exports in `__init__.py` only for stable named codes.

---

## Add A Decoder

`StabilizerCode` currently detects syndromes but does not provide a universal
decoder.

A decoder should probably live in a new module instead of inside
`stabilizer_code.py` if it supports multiple algorithms.

Possible API:

```python
correction = decoder.decode(code, syndrome)
decoder.apply(state, correction)
```

Test by injecting each correctable error, reading the syndrome, decoding it,
applying the correction, and checking the logical state.

---

## Add A Documentation Page

Use the current split:

- `docs/getting-started/`: user-facing tutorials
- `docs/theory/`: math and derivations
- `docs/architecture/`: source-level behavior and data flow
- `docs/api-reference.md`: public API details

Update `mkdocs.yml` whenever a page should be visible in navigation.

---

## Add A Test

Prefer tests that assert invariants rather than implementation details.

Good stabilizer tests:

- stabilizer rows commute
- stabilizer rank is correct
- a known codeword has expected stabilizers
- a known error flips expected syndrome bits
- an invalid input raises `ValueError`
- a state remains the same size after temporary ancilla extraction

Good simulator tests:

- Clifford circuits stay in tableau mode
- non-Clifford gates switch to statevector mode
- debug mode accepts valid Clifford circuits
- trace snapshots are independent copies

---

## Backwards Compatibility

Avoid deleting public names. The package currently keeps legacy `codes.py`
helpers while exposing the new `StabilizerCode` instances at top level.

When replacing an old API with a new one:

1. Keep the old import path.
2. Document the preferred new path.
3. Add tests for both paths if behavior is still supported.
4. Only remove compatibility after an explicit versioned deprecation plan.
