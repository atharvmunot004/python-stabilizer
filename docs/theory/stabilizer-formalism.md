# Stabilizer Formalism

Code links for this page:

- Core tableau state: [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)
- Circuit builder: [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py)
- GF(2) helpers: [`stabilizer_python/linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py)

## Why not just use state vectors?

An $n$-qubit state vector has $2^n$ complex amplitudes. Simulating 50 qubits classically is already infeasible — the vector has over a quadrillion entries.

But many states of interest in quantum computing — particularly in quantum error correction — belong to a restricted class called **stabilizer states**. For these states, there is a polynomial-time classical simulation algorithm. This is the content of the **Gottesman–Knill theorem**.

The key insight: instead of storing the state vector, store a compact *description* of the state in terms of the operators that fix it.

---

## The Pauli Group

The single-qubit Pauli operators are:

$$
I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}, \quad
X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad
Y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}, \quad
Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}
$$

They satisfy:

$$XY = iZ, \quad YZ = iX, \quad ZX = iY$$

and anti-commute pairwise: $XZ = -ZX$, etc.

The **$n$-qubit Pauli group** $\mathcal{P}_n$ consists of all $n$-fold tensor products of single-qubit Paulis with an overall phase of $\pm 1$ or $\pm i$:

$$\mathcal{P}_n = \{ \pm 1, \pm i \} \times \{ I, X, Y, Z \}^{\otimes n}$$

For stabilizer simulation we only need phases $\pm 1$ (the $\pm i$ phases cancel out when tracking stabilizer generators), so we represent each Pauli by an $n$-bit $x$-vector, an $n$-bit $z$-vector, and a sign bit.

| $x_q$ | $z_q$ | Pauli on qubit $q$ |
|---|---|---|
| 0 | 0 | $I$ |
| 1 | 0 | $X$ |
| 1 | 1 | $Y$ |
| 0 | 1 | $Z$ |

This binary encoding is exactly what lives in the `x_mat` and `z_mat` arrays of [`StabilizerState`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py).

---

## Stabilizers

A Pauli operator $P$ **stabilizes** a state $|\psi\rangle$ if:

$$P|\psi\rangle = |\psi\rangle$$

**Example:** $Z$ stabilizes $|0\rangle$ because $Z|0\rangle = |0\rangle$. It does *not* stabilize $|1\rangle$ because $Z|1\rangle = -|1\rangle$.

**Example:** $X$ stabilizes $|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$ because $X|+\rangle = |+\rangle$.

---

## The Stabilizer Group

A set of commuting Pauli operators $\{g_1, g_2, \ldots, g_n\}$ that all have $+1$ eigenvalue on a state $|\psi\rangle$ forms the **stabilizer group** of that state. The state is uniquely determined (up to global phase) by its stabilizer group — no state vector required.

For an $n$-qubit stabilizer state, we need exactly $n$ independent generators.

**Example — the $|00\rangle$ state:**

$$g_1 = Z \otimes I = ZI, \quad g_2 = I \otimes Z = IZ$$

Both satisfy $g_i|00\rangle = |00\rangle$. These two generators fully characterize $|00\rangle$.

In the package:

```python
from stabilizer_python import StabilizerState

st = StabilizerState.zero(2)
print(st.format_chp_printstate())
```

```
+XI
+IX
-----------
+ZI
+IZ
```

The bottom half (below the line) are the **stabilizer generators**: $+ZI$ and $+IZ$, exactly as expected. The top half are the **destabilizers** — explained in [The Tableau Representation](tableau.md).

---

## How gates evolve stabilizers

A Clifford gate $U$ transforms a stabilizer $g$ to $UgU^\dagger$. This is the **Heisenberg picture**: instead of evolving the state, evolve the operators.

The Clifford group is exactly the set of unitaries that map Paulis to Paulis under conjugation. This makes it efficient to track:

| Gate | $X \to$ | $Z \to$ |
|---|---|---|
| $H$ | $Z$ | $X$ |
| $S$ | $Y$ | $Z$ |
| $CNOT_{c,t}$ | $X_c \to X_cX_t$ | $Z_t \to Z_cZ_t$ |

**Example — applying H to qubit 0 of $|00\rangle$:**

Before: stabilizers $ZI$, $IZ$.

After $H \otimes I$: $H(ZI)H^\dagger = XI$, so stabilizer becomes $+XI$.

The state is now $|+0\rangle = |+\rangle \otimes |0\rangle$.

```python
st = StabilizerState.zero(2)
st.h(0)
print(st.format_chp_printstate())
```

```
+ZI
+IX
-----------
+XI
+IZ
```

The stabilizer row flipped from $ZI$ to $XI$ — exactly the conjugation rule $HZH^\dagger = X$.

---

## Gottesman–Knill Theorem

> Any quantum circuit consisting of: state preparation in the computational basis, Clifford gates (H, S, CNOT), and Pauli measurements, can be simulated efficiently on a classical computer.

The proof is constructive: the stabilizer tableau is the efficient classical representation, and the gate update rules above are the efficient simulation. That is exactly what this package implements.

**What Clifford circuits can and cannot do:**

- ✅ Prepare Bell states, GHZ states, graph states
- ✅ Encode and decode QEC codes
- ✅ Perform syndrome measurements
- ❌ Achieve universal quantum computation (need non-Clifford gates like T)
- ❌ Provide quantum speedup for generic problems

---

## Commutativity and independence

Two Paulis $P, Q \in \mathcal{P}_n$ either commute ($PQ = QP$) or anticommute ($PQ = -QP$). The rule:

$$P \text{ and } Q \text{ anticommute} \iff \sum_{q} (x_P^q z_Q^q + x_Q^q z_P^q) \equiv 1 \pmod{2}$$

This is just a bitwise inner product over GF(2). The [`linear_algebra.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/linear_algebra.py) module provides GF(2) tools used by tests to check independence of stabilizer generators.

---

## Summary

| Concept | Classical analog | In the package |
|---|---|---|
| Stabilizer state | — | `StabilizerState` |
| Stabilizer generators | Basis vectors | Last $n$ rows of tableau |
| Gate evolution | Matrix multiplication | `h()`, `s()`, `cnot()`, ... |
| Measurement | — | `measure_z()` |
| QEC syndrome | Parity check | `BitFlip3Code.measure_syndrome()` |

**Next:** [The Tableau Representation](tableau.md) — how all of this is stored as bit arrays.

For the source-level module map, see [Architecture](../architecture/index.md).
