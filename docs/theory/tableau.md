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

## Viewing the full tableau

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(3)
Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st)  # GHZ state
print(st.format_tableau_debug())
```

This prints the CHP-style Pauli rows, the raw X and Z bit matrices, and the phase column — useful for debugging and understanding what the tableau looks like after any sequence of gates.

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
