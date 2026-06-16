# Input Processing And Case Handling

This page explains how `stabilizer-python` processes user input and what happens
for valid, invalid, edge, and mixed-backend cases.

---

## Stabilizer State Inputs

### `StabilizerState.zero(n)`

Input:

- `n`: number of qubits

Validation:

- `n` must be at least 1
- invalid `n` raises `ValueError`

Processing:

1. Allocate `2n x n` X and Z matrices full of zero bits.
2. Allocate `2n` phase bits full of zeroes.
3. Set destabilizer row `i` to `+X_i`.
4. Set stabilizer row `n+i` to `+Z_i`.

Result:

- the physical state $|0\cdots0\rangle$
- stabilizers `+ZIIII...`, `+IZIII...`, and so on

---

## Pauli String Inputs

Pauli strings are used by:

- `StabilizerState.from_stabilizer_list(...)`
- `StabilizerCode(...)`
- `read_syndrome(...)`
- `SyndromeExtractor(...)`
- parity-check helpers through check strings

Accepted characters:

- `I`
- `X`
- `Y`
- `Z`

Accepted sign prefixes:

- `+`
- `-`
- omitted sign, interpreted as `+`

Examples:

```python
"ZZI"
"+ZZI"
"-XZZXI"
"+IIIXXXX"
```

### Normalization Rules

For `StabilizerCode`, each generator is stripped, uppercased, and stored with an
explicit sign:

```text
"zzi"   -> "+ZZI"
" +xzi" -> "+XZI"
"-yyi"  -> "-YYI"
```

For syndrome extraction, signs are removed before measurement because a parity
check circuit measures the Pauli support. A failed check is reported by the
measured eigenvalue bit.

### Invalid Cases

These cases raise `ValueError`:

| Input problem | Example |
|---|---|
| empty string | `""` |
| sign only | `"+"` |
| invalid Pauli character | `"+ZAI"` |
| wrong length for code or state | `StabilizerCode(n=3, k=1, generators=["+ZZ"])` |
| wrong number of stabilizers for `from_stabilizer_list` | two generators for a 3-qubit full state |
| identity stabilizer row in `from_stabilizer_list` | `"+III"` in a full stabilizer-state definition |

---

## Gate Inputs

Gate inputs enter through either `Circuit` or `QuantumSimulator`.

### `Circuit`

`Circuit(n_qubits)` validates that `n_qubits >= 1`.

Fluent methods such as `.h(q)`, `.cnot(control, target)`, `.rz(theta, q)`, and
`.mz(q)` append an `Op` object. They do not validate the target against a state
yet, because no state has been supplied.

Validation happens during `Circuit.run(state)`:

1. A `QuantumSimulator` is created or reused.
2. If the target is a `StabilizerState`, the simulator wraps that exact tableau.
3. The simulator checks gate arity and target indices.
4. Unknown `Op.name` values raise `ValueError`.

### `QuantumSimulator.apply(...)`

`QuantumSimulator.apply(name, qubits, params=None)` handles string gate names.

Processing:

1. Look up `name` in the simulator's gate table.
2. Build or retrieve a `Gate` object.
3. Validate arity.
4. Validate each qubit index.
5. Reject duplicate qubit indices for multi-qubit gates.
6. Route by backend:
   - Clifford gate and mode is `"tableau"`: mutate `StabilizerState`
   - non-Clifford gate or already in `"statevector"` mode: use `Statevector`

Invalid cases:

| Case | Result |
|---|---|
| unknown gate name | `ValueError` |
| too few or too many qubits | `ValueError` |
| out-of-range qubit | `ValueError` |
| duplicate targets on a multi-qubit gate | `ValueError` |
| missing parameter for parameterized gate | `ValueError` or constructor error |

---

## Clifford Versus Non-Clifford Routing

Every `Gate` object has `is_clifford`.

If `is_clifford=True` and the simulator is still in tableau mode, the operation
is dispatched to a tableau method such as:

- `h`
- `s`
- `sdg`
- `sx`
- `sxdg`
- `x`
- `y`
- `z`
- `cnot`
- `cz`
- `cy`
- `swap`

If `is_clifford=False`, the simulator calls `_switch_to_statevector()`:

1. Convert the current tableau to a dense vector using stabilizer projectors.
2. Store the vector in `sim.sv`.
3. Set `sim.mode = "statevector"`.
4. Apply the gate matrix to the dense vector.

Once in statevector mode, later Clifford gates also apply as matrices. The
simulator does not switch back to tableau mode automatically.

---

## Measurement Inputs

### Tableau Measurement

`StabilizerState.measure_z(q)` validates `q` with `_check_qubit`.

Then it has two branches:

| Branch | Condition | Behavior |
|---|---|---|
| deterministic | no stabilizer row has X support on `q` | compute the fixed sign by solving for a stabilizer product equal to `Z_q` |
| random | some stabilizer row has X support on `q` | sample 0/1 uniformly, row-reduce around a pivot, then install signed `Z_q` |

Invalid cases:

- `q < 0` raises `ValueError`
- `q >= state.n` raises `ValueError`

### Statevector Measurement

`Statevector.measure_z(qubit)`:

1. Sums probabilities of basis states whose selected bit is 0 or 1.
2. Samples an outcome.
3. Zeroes inconsistent amplitudes.
4. Renormalizes.

---

## StabilizerCode Inputs

`StabilizerCode(n, k, generators, name="", logical_xs=None, logical_zs=None)`
is the main high-level QEC input path.

### Parameter Validation

Validation order:

1. `n` must be at least 1.
2. `k` must satisfy `0 <= k <= n`.
3. `len(generators)` must equal `n-k`.
4. Every generator must have length `n` after stripping an optional sign.
5. Every generator character must be `I`, `X`, `Y`, or `Z`.
6. The generator check matrix must have GF(2) rank `n-k`.
7. Every generator pair must commute under the binary symplectic product.
8. Provided logical operators, if present, must:
   - have exactly `k` entries
   - have length `n`
   - be non-identity
   - commute with all stabilizers
   - not be in the stabilizer span
   - anticommute with the paired logical operator
   - commute with all unpaired logical operators

### Generator Matrix

Each Pauli string becomes a binary vector:

```text
Pauli string: +XZZXI
X bits:       10010
Z bits:       01110
Vector:       [X bits | Z bits]
```

The code uses this representation for:

- rank checks
- commutation checks
- logical operator validation
- normalizer search
- distance search

### Common Failure Cases

| Input | Why it fails |
|---|---|
| `StabilizerCode(3, 1, ["+ZZI"])` | only one generator, expected `n-k = 2` |
| `StabilizerCode(3, 1, ["+ZZI", "+ZZI"])` | generators are dependent |
| `StabilizerCode(2, 0, ["+XX", "+ZI"])` | generators anticommute |
| logical X of `"+III"` | logical operator cannot be identity |
| logical X inside stabilizer span | it is not a non-trivial logical |
| state with wrong `n` passed to `read_syndrome` | data state size does not match the code |

---

## Syndrome Check Inputs

`StabilizerCode.read_syndrome(state)` strips signs from code generators and
passes the check bodies to `syndrome.read_syndrome(state, check_operators)`.

`syndrome.read_syndrome`:

1. Records the original data size.
2. Validates every check string against that data size.
3. Appends one `|0>` ancilla.
4. Measures each mixed Pauli check using `mixed_parity_check`.
5. Removes the ancilla in a `finally` block.

Because removal is in `finally`, the temporary ancilla is removed even when a
check raises an error after allocation.

`SyndromeExtractor` is different: it allocates one or more ancillas once and
keeps them attached to the state for repeated rounds.

---

## Noise And Benchmark Inputs

### Pauli noise

The E2 noise helpers validate probability inputs before mutating the tableau.

| Function family | Validation |
|---|---|
| `apply_bit_flip`, `apply_phase_flip`, `apply_bit_phase_flip`, `apply_depolarizing` | `p` must be in `[0, 1]` |
| `apply_pauli_channel` | `p_x`, `p_y`, and `p_z` must be non-negative and sum to at most 1 |
| `_all` variants | each target qubit is validated by the underlying single-qubit helper |
| `NoisyCircuit` | `gate_error` and `meas_error` must be in `[0, 1]` |

Each sampled error mutates the `StabilizerState` immediately and returns the
Pauli label that was applied.

### EncodedState

`EncodedState(state, code)` expects:

- a physical `StabilizerState`
- a code-like object with `k`, `logical_x(i)`, `logical_z(i)`, and optionally
  `generators`

Logical-qubit indices are checked against `0 <= i < k`. Logical readout returns
`None` when the current stabilizer group does not determine the requested
logical observable.

### benchmark_code

`benchmark_code(code, noise_model, decoder, n_shots, ...)` validates
`n_shots >= 0`. Per shot, it expects:

1. `code.n` to be the physical qubit count.
2. `code.encode(state)` to prepare the logical state in place.
3. `noise_model(state)` to mutate the state or leave it unchanged.
4. `code.read_syndrome(state)` to return a list of syndrome bits.
5. `decoder(syndrome)` to return `(qubit, pauli)` corrections.

Correction Paulis must be `"X"`, `"Y"`, or `"Z"`. Any other correction label
raises `ValueError`. Qubit range is validated by the corresponding tableau gate
method.

`build_lookup_decoder(code, max_errors=...)` validates `max_errors >= 0`, then
enumerates Pauli errors up to that weight and stores the first minimum-weight
correction found for each syndrome.

---

## Qiskit Inputs

`from_qiskit(qc)` accepts a Qiskit `QuantumCircuit`.

Processing:

1. Iterate over `qc.data`.
2. Resolve instruction name.
3. Resolve local qubit indices from Qiskit's flat qubit list.
4. Skip `barrier` and `delay`.
5. Translate common aliases:
   - `cx` -> `cnot`
   - `measure` -> `mz`
   - `u1` -> `p`
   - `u3` -> `u`
6. Extract numeric parameters for parameterized gates.
7. Expand composite instructions through their definition when available.
8. Raise `ValueError` for unknown unsupported instructions.

See [How from_qiskit Works](../qiskit-interop.md) for the full conversion path.

---

## Debug And Trace Cases

`QuantumSimulator(debug=True)` checks tableau invariants after Clifford gates and
measurements while still in tableau mode.

`QuantumSimulator(trace=True)` records a `SimulatorTraceStep` after every gate.
The snapshot type depends on the active backend:

- tableau mode: `StabilizerState.copy()`
- statevector mode: dense statevector copy

`TracedCircuit` records every Clifford operation and measurement when the target
remains tableau-compatible. If a circuit operation forces the simulator into
statevector mode, `TracedCircuit` raises because its purpose is tableau pedagogy.
