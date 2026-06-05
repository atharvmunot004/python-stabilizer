# Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git
```

Install a pinned release, useful for reproducible experiments:

```bash
pip install git+https://github.com/atharvmunot004/python-stabilizer.git@v0.2.0
```

For local development:

```bash
git clone https://github.com/atharvmunot004/python-stabilizer.git
cd python-stabilizer
pip install -e ".[dev]"
```

The `dev` extra installs `pytest` and `qiskit`, which are used by the optional tests and Qiskit interop examples.

## Requirements

- Python `>=3.9`
- Pure Clifford tableau workflows use only the standard library
- Hybrid statevector simulation uses NumPy
- Qiskit interop requires Qiskit

Source links:

- Repository: [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer)
- Package metadata: [`pyproject.toml`](https://github.com/atharvmunot004/python-stabilizer/blob/main/pyproject.toml)
- Public exports: [`stabilizer_python/__init__.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/__init__.py)

## Verify The Install

```bash
python - <<'PY'
from stabilizer_python import Circuit, StabilizerState

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)
print(st.inspect(views=["stabilizers"]))
PY
```

Expected output:

```text
+XX
+ZZ
```

## Common Setup Issues

If `qiskit` imports fail, install the development dependencies:

```bash
pip install -e ".[dev]"
```

If Python imports an older installed version while you are editing the checkout, reinstall editable mode from the repository root:

```bash
pip install -e ".[dev]"
```
