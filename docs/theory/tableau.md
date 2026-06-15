# The Tableau Representation

This page explains exactly how `StabilizerState` stores an $n$-qubit stabilizer state as arrays of bits, and how every gate modifies those arrays. By the end, the source of `tableau.py` should be fully transparent.

Implementation link: [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py)

---

## The Aaronson–Gottesman Tableau

The key reference is [Aaronson & Gottesman (2004)](https://arxiv.org/abs/quant-ph/0406196). The representation in [`StabilizerState`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) stores $2n$ rows and $n$ columns of bits, split into two matrices `x_mat` and `z_mat`, plus a phase vector `r_phase`.

```
          x_mat           z_mat         r_phase
       [n columns]     [n columns]      [1 bit]

row 0   destab_0        destab_0         p_0
row 1   destab_1        destab_1         p_1
 ...
row n-1 destab_{n-1}   destab_{n-1}     p_{n-1}
─────────────────────────────────────────────────
row n   stab_0          stab_0           p_n
row n+1 stab_1          stab_1           p_{n+1}
 ...
row 2n-1 stab_{n-1}    stab_{n-1}       p_{2n-1}
```

- **Rows 0 to n−1**: destabilizer generators
- **Rows n to 2n−1**: stabilizer generators
- Each row encodes one $n$-qubit Pauli operator
- `x_mat[r][q]` and `z_mat[r][q]` together encode the Pauli on qubit $q$ in row $r`
- `r_phase[r]` is 0 for $+1$ sign, 1 for $-1$ sign

The Pauli encoding per qubit:

| `x_mat[r][q]` | `z_mat[r][q]` | Pauli on qubit $q$ |
|:---:|:---:|:---:|
| 0 | 0 | $I$ |
| 1 | 0 | $X$ |
| 1 | 1 | $Y$ |
| 0 | 1 | $Z$ |

---

## Destabilizers — why they exist

The stabilizer generators alone are sufficient to describe the state. So why store destabilizers?

Efficient measurement. During a **random measurement outcome**, we need to update the tableau by row-multiplying stabilizer rows. To do this correctly while maintaining a valid set of $n$ independent generators, we need a "partner" row for each stabilizer that anticommutes with it but commutes with all others. That partner is the destabilizer.

Concretely: destabilizer row $i$ anticommutes with stabilizer row $n+i$, and commutes with all other stabilizer rows.

---

## Initial state: $|00\cdots0\rangle$

```python
StabilizerState.zero(n)
```

For $n$ qubits, the $|0\cdots0\rangle$ state has stabilizers $Z_0, Z_1, \ldots, Z_{n-1}$ and destabilizers $X_0, X_1, \ldots, X_{n-1}$.

```python
# In tableau.py:
for i in range(n):
    x[i][i] = 1        # destabilizer i = X_i
    z[n + i][i] = 1    # stabilizer i   = Z_i
```

For $n = 2$:

```
x_mat:          z_mat:         r_phase:
[1, 0]          [0, 0]           0      ← destab_0 = +XI
[0, 1]          [0, 0]           0      ← destab_1 = +IX
──────────────────────────────────────
[0, 0]          [1, 0]           0      ← stab_0   = +ZI
[0, 0]          [0, 1]           0      ← stab_1   = +IZ
```

```python
from stabilizer_python import StabilizerState
st = StabilizerState.zero(2)
print(st.format_xz_binary_matrices())
```

```
X matrix (4 x 2)      Z matrix (4 x 2)
  1 0                   0 0
  0 1                   0 0
  0 0                   1 0
  0 0                   0 1
```

---

## Gate update rules

Every Clifford gate acts by conjugation: $g_i \to U g_i U^\dagger$. For Pauli operators, conjugation by Clifford gates maps Paulis to Paulis, so the tableau entries just get permuted or XOR'd.

### Hadamard — `h(q)`

$$H X H^\dagger = Z, \quad H Z H^\dagger = X, \quad H Y H^\dagger = -Y$$

For each row $r$: swap `x_mat[r][q]` and `z_mat[r][q]`. If both were 1 (encoding $Y$), flip the phase since $HYH^\dagger = -Y$.

```python
# In tableau.py:
def h(self, q):
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & z:                          # Y → -Y: flip phase
            self.r_phase[r] ^= 1
        self.x_mat[r][q], self.z_mat[r][q] = z, x   # swap
```

**Trace through an example.** Start with $|0\rangle$ (stabilizer $+Z$). Apply $H$:

```
Before: x=0, z=1, phase=0  →  +Z
After:  x=1, z=0, phase=0  →  +X
```

State is now $|+\rangle$. ✓

---

### Phase gate — `s(q)`

$$S X S^\dagger = Y, \quad S Z S^\dagger = Z, \quad S Y S^\dagger = -X$$

For each row: if `x_mat[r][q] == 1` and `z_mat[r][q] == 1` (Pauli is $Y$), flip phase. Then XOR `z_mat[r][q]` with `x_mat[r][q]`.

```python
def s(self, q):
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & z:
            self.r_phase[r] ^= 1    # Y → -X
        self.z_mat[r][q] ^= x       # X → Y (flips z bit), Z → Z
```

---

### CNOT — `cnot(control, target)`

$$CNOT: X_c \to X_c X_t, \quad Z_t \to Z_c Z_t, \quad X_t \to X_t, \quad Z_c \to Z_c$$

For each row:
- `x_mat[r][target]  ^= x_mat[r][control]`
- `z_mat[r][control] ^= z_mat[r][target]`
- Phase update: if `x_mat[r][c] & z_mat[r][t] & (x_mat[r][t] ^ z_mat[r][c] ^ 1)` then flip phase.

The phase update rule comes directly from Aaronson–Gottesman Table 1.

```python
def cnot(self, c, t):
    for r in range(2 * self.n):
        xc, zc = self.x_mat[r][c], self.z_mat[r][c]
        xt, zt = self.x_mat[r][t], self.z_mat[r][t]
        if xc & zt & (xt ^ zc ^ 1):
            self.r_phase[r] ^= 1
        self.x_mat[r][t] ^= xc
        self.z_mat[r][c] ^= zt
```

**Trace through Bell state preparation** — $H$ on q0, then $CNOT_{0,1}$:

After $H$ on q0 of $|00\rangle$: stabilizers are $XI$, $IZ$.

Apply $CNOT_{0,1}$ to $XI$:
- $X_c$ spreads to $X_c X_t$: $XI \to XX$

Apply $CNOT_{0,1}$ to $IZ$:
- $Z_t$ spreads to $Z_c Z_t$: $IZ \to ZZ$

Final stabilizers: $+XX$, $+ZZ$ — the Bell state $|\Phi^+\rangle$. ✓

---

### Pauli gates

Pauli gates act by conjugation: $X P X^\dagger$ flips the sign of $Z$ and $Y$ (anything with a $z$ bit set on qubit $q$). $Z P Z^\dagger$ flips the sign of $X$ and $Y$.

Working notes with a full case-by-case proof and complexity comparison to CHP: [markdown](../proofs/x-gate-proof.md) · [PDF](../proofs/x-gate-proof.pdf).

```python
def x(self, q):
    for r in range(2 * self.n):
        if self.z_mat[r][q] == 1:
            self.r_phase[r] ^= 1

def z(self, q):
    for r in range(2 * self.n):
        if self.x_mat[r][q] == 1:
            self.r_phase[r] ^= 1
```

---

### Derived Clifford gates

The source also includes state-level helpers for additional Clifford gates:

| Method | Implementation strategy |
|---|---|
| `sdg(q)` / `s_dagger(q)` | Direct $S^\dagger$ tableau update |
| `sx(q)` / `sqrt_x(q)` | Direct $\sqrt{X}$ tableau update |
| `sxdg(q)` / `sqrt_x_dagger(q)` | Direct $\sqrt{X}^\dagger$ tableau update |
| `y(q)` | Pauli-Y conjugation sign update |
| `cz(control, target)` | `H(target)`, `CNOT(control, target)`, `H(target)` |
| `cy(control, target)` | `S†(target)`, `CNOT(control, target)`, `S(target)` |
| `swap(q1, q2)` | Three CNOTs |

These methods are available directly on `StabilizerState`; the minimal `Circuit` builder currently exposes only `H`, `S`, `X`, `Z`, `CNOT`, and `MZ`.

---

## Row multiplication — `_rowmult(a, b)`

Row multiplication implements $\text{row}_a \leftarrow \text{row}_a \cdot \text{row}_b$ in the Pauli group. The bits XOR, but the phase requires careful tracking because Pauli multiplication introduces factors of $i$:

$$XZ = iY, \quad ZX = -iY$$

The helper `_row_mult_phase(x1, z1, x2, z2)` returns the exponent of $i$ contributed by one qubit. Summing over all qubits and reducing mod 4 gives the total phase. If the sum is 2 (i.e., $i^2 = -1$), flip the sign bit.

This is used during measurement to maintain a valid tableau after updating rows.

---

## Viewing and inspecting the tableau

The tableau is intentionally visible. The most convenient entrypoint is `inspect()`, which returns formatted text. Use `print(st.inspect())` for terminal output.

```python
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(3)
Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st)  # GHZ state

print(st.inspect())  # default: CHP-style rows only
```

With `views=None` (the default), `inspect()` prints only the `chp` view. This keeps the default readable for terminal and notebook output.

To print the four main views together, request them explicitly:

```python
print(st.inspect(views=["chp", "binary", "phase", "debug"]))
```

That verbose form is useful in notebooks, examples, and debugging sessions where you want every representation in one place. For narrower output, pass only the view names you need.

### `chp`: signed Pauli rows

```python
print(st.inspect(views=["chp"]))
```

```text
+ZII
+IXI
+IIX

----
+XXX
+ZZI
+ZIZ
```

This is the same output as `format_chp_printstate()`. Rows above the separator are destabilizers. Rows below the separator are stabilizer generators.

### `binary`: raw X and Z matrices

```python
print(st.inspect(views=["binary"]))
```

```text
X matrix (6 x 3)    Z matrix (6 x 3)
  0 0 0               1 0 0
  0 1 0               0 0 0
  0 0 1               0 0 0
  1 1 1               0 0 0
  0 0 0               1 1 0
  0 0 0               1 0 1
```

This is the same output as `format_xz_binary_matrices()`. It is the closest view to the internal data structure: each row is a Pauli operator, and each column is a qubit.

### `phase`: row sign bits

```python
print(st.inspect(views=["phase"]))
```

```text
Phase matrix (6 x 1)
  [0]
  [0]
  [0]
  [0]
  [0]
  [0]
```

This is the same output as `format_phase_matrix()`. A phase bit of `0` means the row has a `+` sign; a phase bit of `1` means the row has a `-` sign.

### `debug`: CHP rows plus matrices

```python
print(st.inspect(views=["debug"]))
```

This is the same output as `format_tableau_debug()`. It combines the CHP-style rows, raw X/Z matrices, and phase column in one block.

### `stabilizers`: only rows `n..2n-1`

```python
print(st.inspect(views=["stabilizers"]))
```

```text
+XXX
+ZZI
+ZIZ
```

Use this when you only want the generators that define the quantum state. For the GHZ state above, the stabilizers are $+XXX$, $+ZZI$, and $+ZIZ$.

For programmatic access, use `stabilizer_strings()`:

```python
st.stabilizer_strings()
# ['+XXX', '+ZZI', '+ZIZ']
```

For raw tableau data instead of labels, use `stabilizer_generators()`. It returns
`(phase_bit, x_row, z_row)` tuples for the stabilizer rows.

### `destabilizers`: only rows `0..n-1`

```python
print(st.inspect(views=["destabilizers"]))
```

```text
+ZII
+IXI
+IIX
```

Use this when debugging measurement updates. Destabilizers are not usually part of the mathematical state description, but they are essential to the Aaronson-Gottesman measurement algorithm.

For programmatic access, use `destabilizer_strings()`:

```python
st.destabilizer_strings()
# ['+ZII', '+IXI', '+IIX']
```

For raw tuple access, use `destabilizer_generators()`. It returns the same
`(phase_bit, x_row, z_row)` structure as `stabilizer_generators()`, but for rows
`0..n-1`.

To read both sides of the tableau as signed Pauli strings in one call, use
`tableau_dict()`:

```python
st.tableau_dict()
# {
#     'stabilizers': ['+XXX', '+ZZI', '+ZIZ'],
#     'destabilizers': ['+ZII', '+IXI', '+IIX'],
# }
```

### Combining views

The `views` argument is ordered. This prints exactly the selected views in the requested order:

```python
print(st.inspect(views=["chp", "binary", "phase"]))
```

Supported view keys are:

| Key | Meaning | Equivalent method |
|---|---|---|
| `chp` | Signed Pauli rows with destabilizer/stabilizer separator | `format_chp_printstate()` |
| `binary` | Raw X and Z bit matrices | `format_xz_binary_matrices()` |
| `phase` | Phase-bit column | `format_phase_matrix()` |
| `debug` | CHP rows + X/Z matrices + phase column | `format_tableau_debug()` |
| `stabilizers` | Stabilizer rows only (`n..2n-1`) | `stabilizer_strings()` |
| `destabilizers` | Destabilizer rows only (`0..n-1`) | `destabilizer_strings()` |

If a view name is unknown, `inspect()` raises `ValueError`.

### Constructing a tableau from stabilizer strings

`from_stabilizer_list()` builds a tableau from signed Pauli labels:

```python
st = StabilizerState.from_stabilizer_list(["+XX", "+ZZ"])
print(st.stabilizer_strings())
```

```text
['+XX', '+ZZ']
```

Signs are optional and default to `+`:

```python
StabilizerState.from_stabilizer_list(["XX", "ZZ"])
```

---

## Comparison with Qiskit's `Clifford`

Qiskit represents Clifford states with [`qiskit.quantum_info.Clifford`](https://docs.quantum.ibm.com/api/qiskit/qiskit.quantum_info.Clifford). Like this package, it keeps **stabilizers** and **destabilizers** as separate generator sets. The physics is the same; the storage layout differs.

### Qiskit's layout

`Clifford` wraps a `StabilizerTable` with two `PauliTable` sub-tables:

| Qiskit attribute | Meaning | Shape |
|---|---|---|
| `cliff.stabilizer` | Stabilizer generators | `(n, 2n)` |
| `cliff.destabilizer` | Destabilizer generators | `(n, 2n)` |
| `cliff.stabilizer.phase` | Stabilizer sign bits | `(n,)` |
| `cliff.destabilizer.phase` | Destabilizer sign bits | `(n,)` |

Each `PauliTable` row stores Pauli bits in **`[X | Z]` column order**: columns `0..n-1` are X bits, columns `n..2n-1` are Z bits. Phase is stored separately as a boolean array, not inside the bit matrix.

Access pattern:

```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

cliff = Clifford(qc)
print(cliff.stabilizer)      # PauliTable for stabilizer rows
print(cliff.destabilizer)    # PauliTable for destabilizer rows
print(cliff.to_labels(mode="S"))  # e.g. ['+XX', '+ZZ']
print(cliff.to_labels(mode="D"))  # destabilizer labels
```

### Our layout

`StabilizerState` follows Aaronson–Gottesman CHP-style storage:

| Our attribute | Meaning | Shape |
|---|---|---|
| `x_mat` | X bits for all `2n` tableau rows | `(2n, n)` |
| `z_mat` | Z bits for all `2n` tableau rows | `(2n, n)` |
| `r_phase` | Sign bits for all `2n` rows | `(2n,)` |

Rows `0..n-1` are destabilizers. Rows `n..2n-1` are stabilizers. X and Z live in **separate** matrices instead of one combined `[X|Z]` row.

Equivalent read APIs:

```python
st.stabilizer_strings()       # like cliff.to_labels(mode="S")
st.destabilizer_strings()     # like cliff.to_labels(mode="D")
st.tableau_dict()             # both sides in one dict
st.stabilizer_generators()    # raw (phase, x_row, z_row) tuples
st.destabilizer_generators()  # raw tuples for destabilizer rows
```

### Row correspondence

For an `n`-qubit state, Qiskit row `i` in `.stabilizer` matches our tableau row `n + i`. Qiskit row `i` in `.destabilizer` matches our tableau row `i`.

| Generator set | Qiskit source | Our source |
|---|---|---|
| Stabilizer row `i` | `cliff.stabilizer[i]` | `x_mat[n+i]`, `z_mat[n+i]`, `r_phase[n+i]` |
| Destabilizer row `i` | `cliff.destabilizer[i]` | `x_mat[i]`, `z_mat[i]`, `r_phase[i]` |

To compare Pauli **content**, translate Qiskit's combined row into separate X/Z lists:

```python
# Qiskit stabilizer row i -> our stabilizer row n + i
x_row = cliff.stabilizer[i, :n].tolist()
z_row = cliff.stabilizer[i, n:].tolist()
phase = int(cliff.stabilizer.phase[i])  # 0 -> +, 1 -> -
```

Direct NumPy array comparison against `x_mat` / `z_mat` requires reshaping: Qiskit packs `[X|Z]` horizontally into one `(n, 2n)` matrix, while we store X and Z as two `(2n, n)` matrices. The bits match after accounting for row offset and column layout.

### What stays aligned

- Stabilizer **labels** from Qiskit `to_labels(mode="S")` match `stabilizer_strings()` for the same Clifford circuit.
- Destabilizer **labels** from `to_labels(mode="D")` match `destabilizer_strings()`.
- Gate semantics are aligned through `from_qiskit()` for supported Clifford gates.

The main practical difference is API shape: Qiskit exposes two `(n, 2n)` Pauli tables plus separate phase vectors; we expose two `(2n, n)` bit matrices plus one phase vector over all rows.

For loading Qiskit circuits into this simulator, see [Qiskit Interop](../getting-started/qiskit.md).

---

## Summary

| Operation | What changes in the tableau |
|---|---|
| `h(q)` | Swap `x` and `z` columns at `q`; flip phase where both were 1 |
| `s(q)` | XOR `z[q]` with `x[q]`; flip phase where both were 1 |
| `cnot(c,t)` | XOR `x[t]` with `x[c]`; XOR `z[c]` with `z[t]`; phase update |
| `x(q)` | Flip phase of rows where `z[q] == 1` |
| `z(q)` | Flip phase of rows where `x[q] == 1` |
| `measure_z(q)` | See [Measurement](measurement.md) |

**Next:** [Measurement](measurement.md) — the most non-trivial operation in the tableau.

For the full source map, see [Architecture](../architecture.md).
