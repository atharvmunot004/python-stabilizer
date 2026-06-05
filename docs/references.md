# References

Curated references for stabilizer formalism, the Gottesman–Knill theorem, QEC codes, and simulation tools. Annotated for what each is actually useful for.

---

## Foundational papers

### Aaronson & Gottesman (2004)
**"Improved Simulation of Stabilizer Circuits"**  
*Physical Review A 70, 052328*  
[arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196)

The primary reference for this package. Introduces the destabilizer formalism that makes measurement $O(n^2)$ instead of $O(n^3)$. The tableau representation, gate update rules, and measurement algorithm in `tableau.py` follow this paper directly. Table 1 of the paper is the gate update rules.

---

### Gottesman (1997)
**"Stabilizer Codes and Quantum Error Correction"**  
*PhD Thesis, Caltech*  
[arXiv:quant-ph/9705052](https://arxiv.org/abs/quant-ph/9705052)

The foundational reference for stabilizer codes. Introduces the stabilizer formalism as a systematic framework for QEC. Chapter 2 covers the Pauli group and stabilizer groups. Chapter 4 covers CSS codes. Essential background before reading Aaronson–Gottesman.

---

### Shor (1995)
**"Scheme for reducing decoherence in quantum computer memory"**  
*Physical Review A 52, R2493*  
[DOI:10.1103/PhysRevA.52.R2493](https://doi.org/10.1103/PhysRevA.52.R2493)

The original 9-qubit code paper. Two pages. The construction in `Shor9Code` implements exactly this.

---

### Calderbank & Shor (1996) / Steane (1996) — CSS codes
**"Good quantum error-correcting codes exist"**  
[arXiv:quant-ph/9602019](https://arxiv.org/abs/quant-ph/9602019)

**"Multiple-particle interference and quantum error correction"**  
[arXiv:quant-ph/9601029](https://arxiv.org/abs/quant-ph/9601029)

CSS (Calderbank–Shor–Steane) codes are a systematic construction of stabilizer codes from classical linear codes. The bit-flip and phase-flip repetition codes are the simplest CSS codes.

---

## Simulation tools

### Gidney (2021) — Stim
**"Stim: a fast stabilizer circuit simulator"**  
*Quantum 5, 497*  
[arXiv:2103.02202](https://arxiv.org/abs/2103.02202)  
[GitHub: quantumlib/Stim](https://github.com/quantumlib/Stim)

The state-of-the-art stabilizer simulator. Orders of magnitude faster than this package for large circuits, with native support for noisy circuits, detector error models, and decoder interfaces. Use Stim for production QEC research; use this package to understand what Stim is doing.

---

### Higgott & Gidney (2023) — PyMatching
**"Sparse Blossom: correcting a million errors per second with minimum-weight matching"**  
[arXiv:2303.15933](https://arxiv.org/abs/2303.15933)  
[GitHub: oscarhiggott/PyMatching](https://github.com/oscarhiggott/PyMatching)

The standard MWPM (minimum-weight perfect matching) decoder for surface codes and related codes. Works natively with Stim detector error models.

---

## Textbooks

### Nielsen & Chuang — *Quantum Computation and Quantum Information*
Cambridge University Press, 2000.

The standard reference. Chapter 10 covers quantum error correction; Section 10.5 covers stabilizer codes specifically. Chapter 4 covers quantum gates including the Clifford group. If you have access to one QC textbook, this is it.

---

### Wilde — *Quantum Information Theory* (2nd ed.)
Cambridge University Press, 2017.  
[Free arXiv version](https://arxiv.org/abs/1106.1445)

More information-theoretic treatment. Chapter 10 covers stabilizer codes with rigorous proofs. Good complement to Nielsen & Chuang.

---

## QEC landscape and decoder benchmarking

### Roffe et al. (2020) — BP-OSD decoder
**"Decoding across the quantum low-density parity-check code landscape"**  
[arXiv:2005.07016](https://arxiv.org/abs/2005.07016)

Introduces belief-propagation with ordered statistics post-processing (BP-OSD), currently the leading decoder for general LDPC codes.

---

### Hesner et al. (2024) — Benchmark metric
**"Average detector likelihood as a metric for the performance of quantum error correction"**  
[arXiv:2408.02082](https://arxiv.org/abs/2408.02082)

Proposes a standardized metric for comparing QEC decoder performance independent of code and noise model. Relevant background for decoder benchmarking methodology.

---

### Riverlane — *QEC Report 2025*
[riverlane.com/qec-report](https://www.riverlane.com/qec-report)

Annual industry report on the state of QEC and decoder development. Good overview of where decoder research stands and what the open problems are.

---

## Source repository resources

The source repository is [`atharvmunot004/python-stabilizer`](https://github.com/atharvmunot004/python-stabilizer). Useful entry points:

- [`stabilizer_python/tableau.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/tableau.py) — Aaronson-Gottesman tableau implementation
- [`stabilizer_python/circuit.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/circuit.py) — fluent circuit builder
- [`stabilizer_python/codes.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/stabilizer_python/codes.py) — QEC examples
- [`tests/test_random_circuits.py`](https://github.com/atharvmunot004/python-stabilizer/blob/main/tests/test_random_circuits.py) — random circuit and tableau invariant tests
- [`docs/architecture.md`](https://github.com/atharvmunot004/python-stabilizer/blob/main/docs/architecture.md) — source-level documentation map

If present in the source repository, a `references/` folder may contain supplementary notebooks and PDFs:

- `Gottesman-Knill Theorem Part 1 & 2` — worked derivations of the theorem
- `Stabilizer Formalism.pdf` — lecture-style notes on the formalism
- `Stabilizer Codes.pdf` — code construction reference

The `docs/proofs/` folder contains working notes linked from the theory pages, for example [X gate tableau update proof](proofs/x-gate-proof.md) ([PDF](proofs/x-gate-proof.pdf)).

These are available in the source repository but not included in the installed package.
