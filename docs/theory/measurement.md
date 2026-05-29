# Measurement

Measurement is the most subtle operation in stabilizer simulation. Unlike gates, which just permute tableau entries, a Z-measurement has two fundamentally different cases depending on whether the outcome is **deterministic** or **random**.

---

## Z-measurement in quantum mechanics

Measuring qubit $q$ in the Z basis projects the state onto either $|0\rangle$ (outcome 0, eigenvalue $+1$) or $|1\rangle$ (outcome 1, eigenvalue $-1$).

From the stabilizer perspective:
- The measurement operator is $Z_q$
- $Z_q$ either **commutes** or **anticommutes** with each stabilizer generator
- This determines which case we are in

---

## Case 1: Deterministic outcome

If $Z_q$ **commutes** with all stabilizer generators, the outcome is fixed — the state is already an eigenstate of $Z_q$.

To find the outcome: there exists some product of stabilizer generators that equals $\pm Z_q$. The sign of that product is the measurement outcome.

In the tableau, this is detected by checking whether any stabilizer row has `x_mat[r][q] == 1` (a Pauli with $X$ or $Y$ on qubit $q$ anticommutes with $Z_q$). If no such row exists, outcome is deterministic.

```python
# In measure_z():
p = -1
for r in range(n, 2 * n):
    if self.x_mat[r][q] == 1:
        p = r
        break

if p == -1:
    # Deterministic case
    outcome = 0
    for r in range(0, n):
        if self.x_mat[r][q] == 1:
            outcome ^= self.r_phase[n + r]
    return outcome
```

The XOR over destabilizer rows that have $X$ on qubit $q$ reconstructs the sign of the implied $Z_q$ stabilizer. This is the Aaronson–Gottesman deterministic measurement algorithm.

**Example:** $|00\rangle$ with stabilizers $ZI$, $IZ$. Measure qubit 0.

$Z_0 = ZI$ commutes with both generators (in fact equals the first one). No anticommuting row → deterministic. Outcome is the phase of $ZI$, which is $+1$ → outcome = 0. ✓

---

## Case 2: Random outcome

If $Z_q$ **anticommutes** with at least one stabilizer generator (row $p$ has `x_mat[p][q] == 1`), the outcome is genuinely random — equiprobable 0 or 1.

After measuring with outcome $m \in \{0, 1\}$:

1. **Pick a random outcome** $m$.
2. **Update the tableau**: the post-measurement state has $Z_q$ (with sign $(-1)^m$) as a new stabilizer replacing the old generator that anticommuted with it.
3. **Maintain independence**: clear $X$ on qubit $q$ from all other rows that had it, using row multiplication with row $p$.

```python
# Random outcome
outcome = random.randint(0, 1)

# Clear X on q from all other rows
for r in range(2 * n):
    if r != p and self.x_mat[r][q] == 1:
        self._rowmult(r, p)

# Move pivot to canonical stabilizer slot n+q
self._rowswap(p, n + q)

# New stabilizer: Z_q with outcome sign
for j in range(n):
    self.x_mat[n + q][j] = 0
    self.z_mat[n + q][j] = 0
self.z_mat[n + q][q] = 1
self.r_phase[n + q] = outcome

# New destabilizer: X_q (anticommutes with Z_q)
for j in range(n):
    self.x_mat[q][j] = 0
    self.z_mat[q][j] = 0
self.x_mat[q][q] = 1
self.r_phase[q] = 0
```

**Example:** Bell state $|\Phi^+\rangle$ with stabilizers $XX$, $ZZ$. Measure qubit 0.

$Z_0 = ZI$ anticommutes with $XX$ (since $X$ anticommutes with $Z$ on qubit 0). So outcome is random.

- If outcome = 0: post-measurement state has stabilizer $+ZI$, implying qubit 0 is $|0\rangle$ and qubit 1 is $|0\rangle$.
- If outcome = 1: post-measurement state has stabilizer $-ZI$, implying qubit 0 is $|1\rangle$ and qubit 1 is $|1\rangle$.

Both cases give a correlated outcome — exactly Bell state entanglement. ✓

---

## Trace through: measuring a Bell state

```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)

print("Before measurement:")
print(st.format_chp_printstate())

outcome = st.measure_z(0)
print(f"\nOutcome: {outcome}")
print("\nAfter measurement:")
print(st.format_chp_printstate())
```

Before:
```
+XI
+IX
-----------
+XX
+ZZ
```

After (outcome = 0):
```
+XI
+ZI
-----------
+ZI
+ZZ   (becomes +IZ once row-reduced)
```

The stabilizers now fix both qubits to the same computational basis state.

---

## Reset

`reset_z(q)` is simply: measure, then apply $X$ if the outcome was 1. This unconditionally leaves qubit $q$ in $|0\rangle$.

```python
def reset_z(self, q):
    m = self.measure_z(q)
    if m == 1:
        self.x(q)
    return m
```

Used in syndrome measurement circuits to recycle ancilla qubits between rounds.

---

## Why phase tracking matters here

During `_rowmult(a, b)`, the phase of the product row must be computed carefully. Pauli multiplication introduces factors of $i$:

$$X \cdot Z = iY$$

Tracking these factors correctly is what `_row_mult_phase()` does — summing the exponents of $i$ over all qubits, then reducing mod 4. An incorrect phase here would give wrong syndrome bits in QEC.

---

## Summary

| Condition | Outcome | Tableau change |
|---|---|---|
| $Z_q$ commutes with all stabilizers | Deterministic (computed from phases) | No change |
| $Z_q$ anticommutes with a stabilizer | Random (uniform) | Replace anticommuting row with $\pm Z_q$; clear X from all other rows |

**Next:** [Error-Correcting Codes](qec-codes.md) — how measurement is used to detect and correct errors.
