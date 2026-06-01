# Error-Correcting Codes

Quantum error correction (QEC) is the primary application of stabilizer formalism. The stabilizer framework makes QEC codes almost natural to describe: a code is just a stabilizer group, a syndrome is a pattern of measurement outcomes, and correction is applying the right Pauli to restore the state.

Implementation links:

- QEC helpers: [`stabilizer_python/codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py)
- Tableau operations used by syndrome extraction: [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)
- QEC tests: [`tests/test_bitflip3.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_bitflip3.py)

---

## The stabilizer code framework

An $[[n, k, d]]$ stabilizer code encodes $k$ logical qubits into $n$ physical qubits with distance $d$.

- **$n$ physical qubits**: the actual qubits we simulate
- **$k$ logical qubits**: the information we're protecting
- **$n - k$ stabilizer generators**: parity checks that detect errors
- **Distance $d$**: minimum number of errors needed to cause an undetectable logical error

The stabilizer generators are Pauli operators that all commute with each other and have $+1$ eigenvalue on the code space. Any error that anticommutes with a generator is detectable.

---

## 3-qubit Bit-flip Code

The 3-qubit repetition code protects one logical bit against a single bit-flip error. It is best understood as a pedagogical code for $X$ errors rather than a complete quantum code: it does not detect or correct arbitrary single-qubit Pauli errors.

### Encoding

Logical states:

$$|0_L\rangle = |000\rangle, \qquad |1_L\rangle = |111\rangle$$

Stabilizer generators:

$$g_1 = Z_0 Z_1, \qquad g_2 = Z_1 Z_2$$

These commute and both have $+1$ eigenvalue on $|000\rangle$ and $|111\rangle$.

Encoder circuit: start with $|\psi\rangle$ on qubit 0, $|0\rangle$ on qubits 1 and 2.

$$\text{CNOT}_{0,1} \cdot \text{CNOT}_{0,2}$$

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import BitFlip3Code

st = StabilizerState.zero(3)
BitFlip3Code.encoder_circuit().run(st)
print(st.format_chp_printstate())
```

```
+XXI
+IXX
-----------
+ZZI
+IZZ
```

Stabilizers $ZZI$ and $IZZ$ — exactly $g_1 = Z_0Z_1$ and $g_2 = Z_1Z_2$. ✓

---

### Syndrome measurement

To detect a bit-flip ($X$) error, measure both stabilizers. An $X$ error on qubit $q$ anticommutes with the generators that include $Z_q$:

| Error | $Z_0Z_1$ | $Z_1Z_2$ | Syndrome $(s_{01}, s_{12})$ |
|:---:|:---:|:---:|:---:|
| None | $+1$ | $+1$ | $(0, 0)$ |
| $X_0$ | $-1$ | $+1$ | $(1, 0)$ |
| $X_1$ | $-1$ | $-1$ | $(1, 1)$ |
| $X_2$ | $+1$ | $-1$ | $(0, 1)$ |

Syndrome bit convention: 0 means $+1$ eigenvalue, 1 means $-1$ eigenvalue.

```python
# Encode |0_L> in 5 qubits (3 data + 2 ancilla)
st = StabilizerState.zero(5)
BitFlip3Code.encoder_circuit().run(st)

# Inject error
st.x(1)   # error on qubit 1

# Measure syndrome
s01, s12 = BitFlip3Code.measure_syndrome(st)
print(f"Syndrome: ({s01}, {s12})")   # (1, 1) → error on q1

# Correct
BitFlip3Code.correct_x_from_syndrome(st, s01, s12)
```

---

### How `measure_syndrome` works

```python
# In codes.py:
def measure_syndrome(state, *, ancilla_01=3, ancilla_12=4):
    # Z0Z1 parity via ancilla q3
    state.cnot(0, ancilla_01)
    state.cnot(1, ancilla_01)
    s01 = state.measure_z(ancilla_01)
    state.reset_z(ancilla_01)

    # Z1Z2 parity via ancilla q4
    state.cnot(1, ancilla_12)
    state.cnot(2, ancilla_12)
    s12 = state.measure_z(ancilla_12)
    state.reset_z(ancilla_12)

    return s01, s12
```

The ancilla qubits start in $|0\rangle$ and are used to extract syndrome bits without measuring the data qubits directly. CNOTs fan parity information onto the ancilla, and then measuring the ancilla in $Z$ reads out the stabilizer eigenvalue.

After measurement, `reset_z` returns the ancilla to $|0\rangle$ for reuse.

---

### What this code cannot correct

The 3-qubit bit-flip code only corrects $X$ (bit-flip) errors. A $Z$ (phase-flip) error on any qubit commutes with both stabilizers $Z_0Z_1$ and $Z_1Z_2$, so it is **undetectable** — the syndrome is $(0, 0)$ even with an error present.

Correcting both $X$ and $Z$ errors requires a more sophisticated code.

---

## 9-qubit Shor Code — $[[9, 1, 3]]$

The Shor code concatenates two layers of repetition to correct any single-qubit error.

### Structure

- **Outer layer**: phase-flip code across 3 block roots (qubits 0, 3, 6)
- **Inner layer**: bit-flip repetition within each block

Qubit layout:

```
Block 0: q0, q1, q2
Block 1: q3, q4, q5
Block 2: q6, q7, q8
```

Logical states:

$$|0_L\rangle = \frac{(|000\rangle + |111\rangle)^{\otimes 3}}{2\sqrt{2}}$$

$$|1_L\rangle = \frac{(|000\rangle - |111\rangle)^{\otimes 3}}{2\sqrt{2}}$$

---

### Encoder circuit

```python
# In codes.py:
def encoder_circuit():
    c = Circuit(9)
    # Spread to block roots
    c.cnot(0, 3).cnot(0, 6)
    # Switch block roots to X basis (outer phase protection)
    c.h(0).h(3).h(6)
    # Bit-flip encoding within each block
    c.cnot(0, 1).cnot(0, 2)
    c.cnot(3, 4).cnot(3, 5)
    c.cnot(6, 7).cnot(6, 8)
    return c
```

Step by step:
1. CNOT fans $|\psi\rangle$ to the three block roots, creating a superposition across blocks.
2. $H$ on each root switches from $Z$ basis to $X$ basis — this is the outer phase-flip code.
3. CNOTs within each block create the inner bit-flip repetition.

---

### Stabilizer generators

The Shor code has 8 stabilizer generators (9 physical qubits encoding 1 logical):

**Bit-flip stabilizers** (within each block):
$$Z_0Z_1, \; Z_1Z_2, \; Z_3Z_4, \; Z_4Z_5, \; Z_6Z_7, \; Z_7Z_8$$

**Phase-flip stabilizers** (across blocks):
$$X_0X_1X_2X_3X_4X_5, \; X_3X_4X_5X_6X_7X_8$$

The bit-flip stabilizers detect $X$ errors within each block. The phase-flip stabilizers detect $Z$ errors across blocks.

---

### Error correction

```python
from stabilizer_python import StabilizerState
from stabilizer_python.codes import Shor9Code

st = StabilizerState.zero(9)
Shor9Code.encoder_circuit().run(st)

# Inject an X error
st.x(4)

# Read syndrome
syndrome = Shor9Code.read_syndrome(st)

# Correct
Shor9Code.correct_x_from_syndrome(st, syndrome)
```

The syndrome is the tuple of phase bits from all 9 stabilizer generators in this simulator's tableau. Each single-qubit $X$ error produces a unique syndrome pattern for the current encoded layout. These patterns are stored in [`_X_SYNDROME`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py), allowing the implemented helper to identify and fix the affected qubit.

---

## Why Shor's code corrects any single-qubit error

Any single-qubit error can be decomposed into Pauli components: $I$, $X$, $Y$, $Z$.

- $X$ errors: detected and corrected by the bit-flip stabilizers within each block.
- $Z$ errors: detected and corrected by the phase-flip stabilizers across blocks.
- $Y = iXZ$: both components are detected; correcting $X$ and $Z$ separately also corrects $Y$.
- $I$ (no error): syndrome is all zeros, no correction applied.

The concatenated structure means a single physical qubit error can never affect more than one block and one inter-block relationship simultaneously — keeping it below the detection threshold.

The current package implements the encoder and an `X`-error correction helper. The stabilizer-code theory above explains the full Shor-code protection mechanism; adding explicit `Z` and `Y` correction helpers would be a natural extension point.

---

## Comparing the two codes

| Property | BitFlip3 | Shor9 |
|---|---|---|
| Physical qubits | 3 | 9 |
| Logical qubits | 1 | 1 |
| Full quantum distance | Not a full arbitrary-Pauli code | 3 |
| Corrects $X$ | ✅ | ✅ |
| Corrects $Z$ | ❌ | Theoretically yes; helper not implemented |
| Corrects $Y$ | ❌ | Theoretically yes; helper not implemented |
| Stabilizers | 2 | 8 |
| Main source class | [`BitFlip3Code`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) | [`Shor9Code`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) |

---

## Further reading

- [References](../references.md) — key papers on stabilizer codes and QEC
- For LDPC codes, surface codes, and beyond: see the decoder benchmarking resources in references

**Next:** [API Reference](../api-reference.md)
