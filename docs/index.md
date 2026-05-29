# stabilizer-python

A minimal, dependency-free stabilizer (Clifford) simulator in pure Python — built to be read, not just used.

If you want to understand **how** stabilizer simulation works at the bit level, this is the right place. Every gate, measurement, and QEC routine maps directly to the theory, and the code is written to make that connection obvious.

---

## What's included

| Module | What it does |
|---|---|
| `StabilizerState` | Aaronson–Gottesman tableau: the core state representation |
| `Circuit` | Fluent gate builder that runs on a `StabilizerState` |
| `codes` | `BitFlip3Code` and `Shor9Code` — full encode/syndrome/correct pipelines |
| `linear_algebra` | GF(2) Gaussian elimination and rank |

---

## Installation

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

No Qiskit required. Pure Python, `>=3.9`.

Optional dev dependencies (pytest + Qiskit interop tests):

```bash
pip install "stabilizer-python[dev] @ git+https://github.com/atharvmunot004/python-stabilizer.git"
```

---

## Quick start

### Bell state

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(2)
c = Circuit(2).h(0).cnot(0, 1)
c.run(st)

print(st.format_chp_printstate())
```

Output:
```
+XI
+IX
-----------
+XX
+ZZ
```

The stabilizers `+XX` and `+ZZ` are exactly the generators of the Bell state $|\Phi^+\rangle$.

---

### 3-qubit bit-flip correction

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code

# Encode |0_L>
st = StabilizerState.zero(5)   # 3 data + 2 ancilla
BitFlip3Code.encoder_circuit().run(st)

# Inject an X error on qubit 1
st.x(1)

# Measure syndrome
s01, s12 = BitFlip3Code.measure_syndrome(st)
print(f"Syndrome: ({s01}, {s12})")  # (1, 1) → error on q1

# Correct
BitFlip3Code.correct_x_from_syndrome(st, s01, s12)
```

---

## Where to go next

- **New to stabilizers?** Start with [Stabilizer Formalism](theory/stabilizer-formalism.md)
- **Understand the tableau?** Read [The Tableau Representation](theory/tableau.md)
- **See how measurement works?** Read [Measurement](theory/measurement.md)
- **QEC codes?** Read [Error-Correcting Codes](theory/qec-codes.md)
- **Just want the API?** Jump to [API Reference](api-reference.md)
