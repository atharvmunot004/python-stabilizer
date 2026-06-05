# Your First Tableau State

The core object is `StabilizerState`. It stores a stabilizer tableau: X bits, Z bits, and phase bits for `2n` Pauli rows.

```python
from stabilizer_python import StabilizerState

st = StabilizerState.zero(2)
print(st.inspect(views=["chp"]))
```

Output:

```text
+XI
+IX

---
+ZI
+IZ
```

The top half are **destabilizers**. The bottom half are **stabilizer generators**.

For `|00>`, the stabilizers are:

$$
Z_0, \quad Z_1
$$

That is why the bottom rows are `+ZI` and `+IZ`.

## What The Bits Mean

Internally, every row stores a Pauli string using one X bit and one Z bit per qubit:

| X bit | Z bit | Pauli |
|:---:|:---:|:---:|
| 0 | 0 | `I` |
| 1 | 0 | `X` |
| 1 | 1 | `Y` |
| 0 | 1 | `Z` |

You can see those raw bits with:

```python
print(st.inspect(views=["binary"]))
```

Output:

```text
X matrix (4 x 2)    Z matrix (4 x 2)
  1 0                 0 0
  0 1                 0 0
  0 0                 1 0
  0 0                 0 1
```

And the row signs with:

```python
print(st.inspect(views=["phase"]))
```

Output:

```text
Phase matrix (4 x 1)
  [0]
  [0]
  [0]
  [0]
```

`0` means `+`; `1` means `-`.

## Why This Matters

The simulator never needs to store all amplitudes for a pure Clifford state. It stores only the Pauli generators that describe the state. This is the Gottesman-Knill advantage in practice.

For the full bit-level explanation, see [The Tableau Representation](../theory/tableau.md).
