# Hybrid Simulation

This page explains why `stabilizer-python` has both a tableau backend and a statevector backend, and how the simulator crosses the Clifford/non-Clifford boundary.

## Why two backends?

The tableau backend is exponentially cheaper for Clifford circuits. It stores an `n`-qubit state as binary Pauli generators instead of a `2^n` complex vector, so Clifford gates can update generator bits directly.

That efficiency comes from closure: Clifford gates map Pauli operators to Pauli operators under conjugation. The tableau only needs to track how each generator changes.

Non-Clifford gates break that closure. For example:

```text
T X T† = (X + Y) / sqrt(2)
```

The result is not a single Pauli operator, so there is no single-row tableau update that represents it. Dense statevector simulation is more expensive, but it can apply arbitrary unitary matrices.

---

## The Clifford/non-Clifford boundary

Each `Gate` object has an `is_clifford` flag. That flag is the routing signal used by `QuantumSimulator`.

The boundary is not a user choice:

- If `gate.is_clifford` is true and the simulator is still in tableau mode, `QuantumSimulator` calls the matching `StabilizerState` method.
- Otherwise, `QuantumSimulator` converts the current tableau to a `Statevector` and applies the gate matrix.

The switch is one-way. Once the simulator is in statevector mode, it stays there for all later gates, including Clifford gates.

The reason is practical and mathematical. Converting a statevector back to a tableau is only possible when the current state happens to be a stabilizer state, and checking or reconstructing that representation costs O(2^n). The hybrid design keeps the boundary simple and predictable.

---

## The `tableau_to_statevector` bridge

Given stabilizer generators \(g_1, \ldots, g_n\), the stabilizer state \(|\psi\rangle\) is the unique state satisfying:

\[
g_i |\psi\rangle = |\psi\rangle
\]

for every generator \(g_i\).

Each generator is a signed Pauli operator:

\[
g_i = \pm P_1 \otimes P_2 \otimes \cdots \otimes P_n
\]

where each \(P_j\) is `I`, `X`, `Y`, or `Z`, read from the tableau's `x_mat`, `z_mat`, and `r_phase` rows.

The state can be constructed by applying stabilizer projectors:

\[
|\psi\rangle \propto \prod_i \frac{I + g_i}{2} |0^n\rangle
\]

Each projector `(I + g_i) / 2` is a `2^n x 2^n` matrix built from Kronecker products of single-qubit Pauli matrices. After each projection, the vector is renormalized.

Cost: O(n · 2^n). This is called exactly once at the boundary from tableau mode to statevector mode.

For a two-qubit Bell state, the stabilizer generators are:

```text
g1 = XX
g2 = ZZ
```

The bridge applies:

```text
(I + XX) / 2
(I + ZZ) / 2
```

The resulting normalized state is:

```text
(|00> + |11>) / sqrt(2)
```

---

## Performance implications

| Circuit type | Mode throughout | Per-gate cost | Max practical n |
|---|---|---|---|
| Pure Clifford | Tableau | O(n) | ~10,000 qubits |
| Clifford prefix + one T gate | Tableau then statevector | O(2^n) after switch | ~25-30 qubits |
| Arbitrary unitary | Statevector from start | O(2^n) | ~25-30 qubits |

The tableau prefix before the first `T` gate or rotation is essentially free compared with dense simulation. The cost cliff is at the switch point, not at circuit start.

---

## When to use each class directly

Use `StabilizerState` directly for pure QEC circuits, syndrome extraction, stabilizer code encoding/decoding, and other all-Clifford workflows. It gives you tableau speed and the `format_chp_printstate()` debugging tools.

Use `QuantumSimulator` for any circuit with `T` gates, rotations, Toffoli, arbitrary `Gate` objects, or Qiskit circuits loaded through `from_qiskit`. The Clifford prefix still runs on the tableau backend.

Use `from_qiskit` with `QuantumSimulator` when starting from an existing Qiskit circuit and wanting the tableau speedup on any Clifford prefix before the first non-Clifford operation.
