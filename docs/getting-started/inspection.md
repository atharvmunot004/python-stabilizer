# Inspecting Tableaux

`StabilizerState.inspect()` is the recommended way to print tableau state. It returns a string, so wrap it in `print(...)` for terminal output.

```python
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(3)
Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st)

print(st.inspect())
```

With no arguments, `inspect()` prints the `chp` view only. This keeps the default compact:

```text
+ZII
+IXI
+IIX

----
+XXX
+ZZI
+ZIZ
```

To print all main views, request them explicitly:

```python
print(st.inspect(views=["chp", "binary", "phase", "debug"]))
```

Each view is separated by a blank line.

## View: `chp`

CHP-style signed Pauli rows:

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

Rows above the separator are destabilizers. Rows below the separator are stabilizer generators.

Equivalent direct method:

```python
print(st.format_chp_printstate())
```

## View: `binary`

Raw X and Z bit matrices:

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

Equivalent direct method:

```python
print(st.format_xz_binary_matrices())
```

## View: `phase`

Phase-bit column:

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

`0` means a `+` sign. `1` means a `-` sign.

Equivalent direct method:

```python
print(st.format_phase_matrix())
```

## View: `debug`

Combined CHP rows, X/Z matrices, and phase column:

```python
print(st.inspect(views=["debug"]))
```

Equivalent direct method:

```python
print(st.format_tableau_debug())
```

## View: `stabilizers`

Only rows `n..2n-1`:

```python
print(st.inspect(views=["stabilizers"]))
```

```text
+XXX
+ZZI
+ZIZ
```

Use this when you want the generators that define the quantum state.

For programmatic access as a list, use `stabilizer_strings()`:

```python
print(st.stabilizer_strings())
# ['+XXX', '+ZZI', '+ZIZ']
```

## View: `destabilizers`

Only rows `0..n-1`:

```python
print(st.inspect(views=["destabilizers"]))
```

```text
+ZII
+IXI
+IIX
```

Use this when debugging tableau measurement updates. Destabilizers are not usually listed in textbook state descriptions, but they are essential to efficient measurement simulation.

For programmatic access as a list, use `destabilizer_strings()`:

```python
print(st.destabilizer_strings())
# ['+ZII', '+IXI', '+IIX']
```

## Combining Views

Pass view names in the exact order you want:

```python
print(st.inspect(views=["chp", "binary", "phase"]))
print(st.inspect(views=["stabilizers", "destabilizers"]))
```

Supported view keys:

| Key | Output |
|---|---|
| `chp` | Same as `format_chp_printstate()` |
| `binary` | Same as `format_xz_binary_matrices()` |
| `phase` | Same as `format_phase_matrix()` |
| `debug` | Same as `format_tableau_debug()` |
| `stabilizers` | Only tableau rows `n..2n-1` as signed Pauli strings |
| `destabilizers` | Only tableau rows `0..n-1` as signed Pauli strings |

Unknown view names raise `ValueError`:

```python
st.inspect(views=["chp", "not-a-view"])  # ValueError
```

## Constructing From Stabilizer Labels

Use `from_stabilizer_list()` when you already have signed Pauli labels:

```python
st = StabilizerState.from_stabilizer_list(["+XX", "+ZZ"])
print(st.stabilizer_strings())
# ['+XX', '+ZZ']
```

Signs are optional and default to `+`:

```python
st = StabilizerState.from_stabilizer_list(["XX", "ZZ"])
```

For the theory behind these rows and matrices, see [The Tableau Representation](../theory/tableau.md).
