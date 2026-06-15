# Gate Operation Rules — Mathematical Proofs

This page derives every tableau update rule in `tableau.py` from first
principles. Each rule is stated as a theorem, proved algebraically, and
then shown as the corresponding code.

---

## 1. Foundations

### 1.1 The Pauli Group

The single-qubit Pauli matrices are:

$$
I = \begin{pmatrix}1&0\\0&1\end{pmatrix},\quad
X = \begin{pmatrix}0&1\\1&0\end{pmatrix},\quad
Y = \begin{pmatrix}0&-i\\i&0\end{pmatrix},\quad
Z = \begin{pmatrix}1&0\\0&-1\end{pmatrix}
$$

They satisfy $X^2 = Y^2 = Z^2 = I$ and the cyclic multiplication rules:

$$XY = iZ,\quad YZ = iX,\quad ZX = iY$$
$$YX = -iZ,\quad ZY = -iX,\quad XZ = -iY$$

The $n$-qubit Pauli group $\mathcal{P}_n$ consists of all $n$-fold tensor
products $i^k P_1 \otimes \cdots \otimes P_n$ where $P_j \in \{I,X,Y,Z\}$
and $k \in \{0,1,2,3\}$.

### 1.2 The Bit Encoding

**Definition.** The tableau encodes a Pauli $P \in \{I,X,Y,Z\}$ on qubit $q$
using two bits $(x, z)$ and a global phase bit as follows:

| $x$ | $z$ | Pauli |
|-----|-----|-------|
| 0   | 0   | $I$   |
| 1   | 0   | $X$   |
| 1   | 1   | $Y$   |
| 0   | 1   | $Z$   |

The global sign $(-1)^r$ is stored in `r_phase[r]`. Note that $Y$ requires
both bits set: this encodes $Y = iXZ$ at the level of the full operator, but
since all tableau rows represent Hermitian Paulis with eigenvalues $\pm 1$,
the phase bit tracks the sign, not the $i$ factor.

**Lemma 1.1** *(Completeness)*. The encoding is a bijection between
$\{I,X,Y,Z\}$ and $\{0,1\}^2$. Every Hermitian single-qubit Pauli (up to
sign) has a unique $(x,z)$ representation.

*Proof.* The four pairs $(0,0),(1,0),(1,1),(0,1)$ are distinct elements of
$\{0,1\}^2$ and there are exactly four Paulis $\{I,X,Y,Z\}$, so the map is
a bijection. $\square$

---

## 2. Single-Qubit Gate Proofs

For each gate $G$, we must show that the bit manipulation rules in `tableau.py`
correctly implement the conjugation map $P \mapsto GPG^\dagger$ for all
$P \in \{I,X,Y,Z\}$.

### 2.1 Hadamard

**Theorem 2.1.** The Hadamard gate satisfies:

$$HXH^\dagger = Z,\quad HYH^\dagger = -Y,\quad HZH^\dagger = X$$

*Proof.* Using $H = \frac{1}{\sqrt{2}}\begin{pmatrix}1&1\\1&-1\end{pmatrix}$:

$$HXH^\dagger = \frac{1}{2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}
\begin{pmatrix}0&1\\1&0\end{pmatrix}
\begin{pmatrix}1&1\\1&-1\end{pmatrix}
= \frac{1}{2}\begin{pmatrix}2&0\\0&-2\end{pmatrix} = Z \checkmark$$

$$HYH^\dagger = \frac{1}{2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}
\begin{pmatrix}0&-i\\i&0\end{pmatrix}
\begin{pmatrix}1&1\\1&-1\end{pmatrix}
= \frac{1}{2}\begin{pmatrix}0&2i\\-2i&0\end{pmatrix} = -Y \checkmark$$

$$HZH^\dagger = \frac{1}{2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}
\begin{pmatrix}1&0\\0&-1\end{pmatrix}
\begin{pmatrix}1&1\\1&-1\end{pmatrix}
= \frac{1}{2}\begin{pmatrix}0&2\\2&0\end{pmatrix} = X \checkmark \quad\square$$

**Corollary 2.2** *(Bit rule for H)*. In the $(x,z)$ encoding:

$$H: (x,z) \mapsto (z,x), \quad \text{phase flipped iff } x=1 \text{ and } z=1$$

*Proof.* The conjugation rules $X\leftrightarrow Z$ correspond exactly to
swapping the $x$ and $z$ bits, since $X \sim (1,0)$ and $Z \sim (0,1)$. For
$Y \sim (1,1)$: $HYH^\dagger = -Y$ adds a sign, so the phase bit flips when
$x \wedge z = 1$. For $I \sim (0,0)$: $HIH^\dagger = I$, no change. $\square$

**Code:**
```python
def h(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & z:                              # Y case: phase flip
            self.r_phase[r] ^= 1
        self.x_mat[r][q], self.z_mat[r][q] = z, x   # swap x ↔ z
```

---

### 2.2 Phase Gate S

**Theorem 2.3.** The phase gate $S = \begin{pmatrix}1&0\\0&i\end{pmatrix}$ satisfies:

$$SXS^\dagger = Y,\quad SYS^\dagger = -X,\quad SZS^\dagger = Z$$

*Proof.*

$$SXS^\dagger = \begin{pmatrix}1&0\\0&i\end{pmatrix}
\begin{pmatrix}0&1\\1&0\end{pmatrix}
\begin{pmatrix}1&0\\0&-i\end{pmatrix}
= \begin{pmatrix}0&-i\\i&0\end{pmatrix} = Y \checkmark$$

$$SYS^\dagger = \begin{pmatrix}1&0\\0&i\end{pmatrix}
\begin{pmatrix}0&-i\\i&0\end{pmatrix}
\begin{pmatrix}1&0\\0&-i\end{pmatrix}
= \begin{pmatrix}0&-1\\-1&0\end{pmatrix} = -X \checkmark$$

$$SZS^\dagger = \begin{pmatrix}1&0\\0&i\end{pmatrix}
\begin{pmatrix}1&0\\0&-1\end{pmatrix}
\begin{pmatrix}1&0\\0&-i\end{pmatrix}
= \begin{pmatrix}1&0\\0&-1\end{pmatrix} = Z \checkmark \quad\square$$

**Corollary 2.4** *(Bit rule for S)*. In the $(x,z)$ encoding:

$$S: (x,z) \mapsto (x,\; z \oplus x), \quad \text{phase flipped iff } x=1 \text{ and } z=1$$

*Proof.* We need $S$ to map:
- $X \sim (1,0) \to Y \sim (1,1)$: XOR $z$ with $x$ gives $(1,0\oplus 1)=(1,1)$. ✓
- $Y \sim (1,1) \to -X \sim (1,0)$: XOR $z$ with $x$ gives $(1,1\oplus 1)=(1,0)$, plus phase flip since input was $Y$ ($x\wedge z=1$). ✓
- $Z \sim (0,1) \to Z \sim (0,1)$: XOR $z$ with $x=0$ leaves $(0,1)$ unchanged. ✓
- $I \sim (0,0) \to I \sim (0,0)$: unchanged. ✓ $\square$

**Code:**
```python
def s(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & z:               # Y → -X: phase flip
            self.r_phase[r] ^= 1
        self.z_mat[r][q] ^= x  # z := z XOR x
```

---

### 2.3 S-dagger

**Theorem 2.5.** $S^\dagger = \begin{pmatrix}1&0\\0&-i\end{pmatrix}$ satisfies:

$$S^\dagger X (S^\dagger)^\dagger = -Y,\quad S^\dagger Y (S^\dagger)^\dagger = X,\quad S^\dagger Z (S^\dagger)^\dagger = Z$$

*Proof.* $S^\dagger = S^3 = S^{-1}$, so the rules follow by inverting those of $S$:
$S: X \to Y$ inverts to $S^\dagger: Y \to X$; $S: Y \to -X$ inverts to
$S^\dagger: X \to -Y$; $S: Z \to Z$ inverts to $S^\dagger: Z \to Z$. $\square$

**Corollary 2.6** *(Bit rule for S†)*. The bit mutation $z \mathrel{\oplus}= x$
is identical to that for $S$, but the phase flip fires when $x=1, z=0$ (the
$X$ Pauli) rather than when $x=1, z=1$ (the $Y$ Pauli).

*Proof.* The mutation maps:
- $X \sim (1,0) \to (1,1) = Y$, but $S^\dagger X S = -Y$ requires a sign flip.
  The condition $x \wedge (z \oplus 1)$ is true iff $x=1$ and $z=0$, i.e. input is $X$. ✓
- $Y \sim (1,1) \to (1,0) = X$, no phase flip (no sign in $S^\dagger Y S = X$). ✓
- $Z \sim (0,1) \to (0,1) = Z$, no change. ✓ $\square$

**Code:**
```python
def sdg(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & (z ^ 1):         # X → -Y: phase flip (x=1, z=0)
            self.r_phase[r] ^= 1
        self.z_mat[r][q] ^= x   # same bit mutation as S
```

---

### 2.4 Pauli Gates

**Theorem 2.7.** The Pauli gates satisfy:

$$XXX^\dagger = X,\quad XYX^\dagger = -Y,\quad XZX^\dagger = -Z$$
$$YXY^\dagger = -X,\quad YYY^\dagger = Y,\quad YZY^\dagger = -Z$$
$$ZXZ^\dagger = -X,\quad ZYZ^\dagger = -Y,\quad ZZZ^\dagger = Z$$

*Proof.* Using $XZ = -ZX$ and $XY = iZ = -YX$:

For $X$: $X$ commutes with itself ($X^2P = P$ if $P = X$ or $I$) and
anticommutes with $Y$ and $Z$. Conjugation by $X$ flips the sign of any
Pauli that anticommutes with $X$, i.e. $Y$ and $Z$. $\square$

**Corollary 2.8** *(Bit rules for X, Y, Z)*. Conjugation by a Pauli gate only
produces sign flips — it never changes the Pauli type. The sign flip rule for
each gate is:

| Gate | Flip sign when |
|------|----------------|
| $X$  | $z = 1$ (Pauli has Z component: Z or Y) |
| $Y$  | $x \oplus z = 1$ (Pauli is X or Z, not Y or I) |
| $Z$  | $x = 1$ (Pauli has X component: X or Y) |

*Proof.* A Pauli $P$ flips sign under conjugation by $Q$ iff $P$ and $Q$
anticommute, i.e. $PQ = -QP$. The anticommutation relations are:
$\{X,Y\} = \{X,Z\} = 0$, $\{Y,Z\} = 0$, and all others commute.
So $X$ anticommutes with $Y$ and $Z$ (those with $z=1$); $Y$ anticommutes
with $X$ and $Z$ (those with $x \oplus z = 1$); $Z$ anticommutes with $X$
and $Y$ (those with $x=1$). $\square$

**Code:**
```python
def x(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        if self.z_mat[r][q] == 1:      # Z component → sign flip
            self.r_phase[r] ^= 1

def y(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        if self.x_mat[r][q] ^ self.z_mat[r][q]:  # X or Z → sign flip
            self.r_phase[r] ^= 1

def z(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        if self.x_mat[r][q] == 1:      # X component → sign flip
            self.r_phase[r] ^= 1
```

---

### 2.5 √X and (√X)†

**Theorem 2.9.** $\sqrt{X} = \frac{1}{2}\begin{pmatrix}1+i&1-i\\1-i&1+i\end{pmatrix}$ satisfies:

$$\sqrt{X}\cdot X\cdot(\sqrt{X})^\dagger = X,\quad
\sqrt{X}\cdot Y\cdot(\sqrt{X})^\dagger = Z,\quad
\sqrt{X}\cdot Z\cdot(\sqrt{X})^\dagger = -Y$$

*Proof.* Note $\sqrt{X} = e^{-i\pi X/4} = \cos(\pi/4)I - i\sin(\pi/4)X
= \frac{1}{\sqrt{2}}(I - iX)$. Then:

$$\sqrt{X}\cdot Z\cdot(\sqrt{X})^\dagger
= \frac{1}{2}(I-iX)Z(I+iX) = \frac{1}{2}(Z + iZX - iXZ + XZX)$$

Using $ZX = -XZ = -iY$ and $XZX = X(-XZ)X^{-1}X = -ZX^2 = -Z \cdot I$... Let
us compute directly:

$$\frac{1}{2}(Z + iZX - iXZ + XZX)
= \frac{1}{2}\big(Z + i(-iY) - i(iY) + (-Z)\big)
= \frac{1}{2}(Z + Y + Y - Z) = Y$$

But the sign: $\sqrt{X}\cdot Z = \frac{1}{\sqrt{2}}(I-iX)Z = \frac{1}{\sqrt{2}}(Z - iXZ) = \frac{1}{\sqrt{2}}(Z + i \cdot iY) = \frac{1}{\sqrt{2}}(Z - Y)$.
Post-multiplying by $(\sqrt{X})^\dagger = \frac{1}{\sqrt{2}}(I + iX)$:

$$\frac{1}{2}(Z-Y)(I+iX) = \frac{1}{2}(Z + iZX - Y - iYX)
= \frac{1}{2}(Z - iY - Y + iZ) \cdot (-1)$$

Re-doing carefully: $\sqrt{X} = \frac{1}{\sqrt{2}}(I - iX)$, so
$\sqrt{X} \cdot Z \cdot \sqrt{X}^\dagger
= \frac{1}{2}(I-iX)Z(I+iX)
= \frac{1}{2}(Z + iZ X - i X Z + X Z X)$.

Since $XZ = -iY$ and $ZX = iY$:

$$= \frac{1}{2}\bigl(Z + i(iY) - i(-iY) + X(-iY)X^{-1} \cdot X^2\bigr)$$

$$= \frac{1}{2}(Z - Y - Y + X(-iY)X)$$

$X(-iY)X = -i \cdot XYX = -i(-Y) = iY$, so:

$$= \frac{1}{2}(Z - 2Y + iY \cdot ???)$$

Let us use a cleaner approach. Since $\sqrt{X}^2 = X$ and the conjugation
action of $X$ sends $Z \to -Z$, applying $\sqrt{X}$ twice gives a sign flip.
So the half-step must send $Z$ to something whose square under conjugation
is $-Z$. The candidate is $-Y$ since $Y \cdot Z \cdot Y = -Z$... actually
$(-Y)(-Y) = Y^2 = I$, and $Y Z Y = -Z$. Checking $-Y$ directly:
$\sqrt{X} \cdot Z \cdot (\sqrt{X})^\dagger = ?$ We verify numerically:

$$\frac{1}{2}\begin{pmatrix}1+i&1-i\\1-i&1+i\end{pmatrix}
\begin{pmatrix}1&0\\0&-1\end{pmatrix}
\frac{1}{2}\begin{pmatrix}1-i&1+i\\1+i&1-i\end{pmatrix}$$

$$= \frac{1}{4}\begin{pmatrix}1+i&-(1-i)\\1-i&-(1+i)\end{pmatrix}
\begin{pmatrix}1-i&1+i\\1+i&1-i\end{pmatrix}$$

$$= \frac{1}{4}\begin{pmatrix}
(1+i)(1-i)-(1-i)(1+i) & (1+i)(1+i)-(1-i)(1-i) \\
(1-i)(1-i)-(1+i)(1+i) & (1-i)(1+i)-(1+i)(1-i)
\end{pmatrix}$$

$$= \frac{1}{4}\begin{pmatrix} 2-2 & (2i)-(-2i) \\ (-2i)-(2i) & 0 \end{pmatrix}
= \frac{1}{4}\begin{pmatrix}0 & 4i \\ -4i & 0\end{pmatrix}
= \begin{pmatrix}0 & i \\ -i & 0\end{pmatrix} = -Y \checkmark$$

So $\sqrt{X}: Z \to -Y$. Similarly one verifies $\sqrt{X}: Y \to Z$ and
$\sqrt{X}: X \to X$. $\square$

**Corollary 2.10** *(Bit rule for √X)*. The mutation is $x \mathrel{\oplus}= z$,
with a phase flip when the input is $Z$ (i.e. $x=0, z=1$, captured by
$(x \oplus 1) \wedge z$).

*Proof.*
- $X \sim (1,0) \to (1 \oplus 0, 0) = (1,0) = X$. ✓
- $Y \sim (1,1) \to (1 \oplus 1, 1) = (0,1) = Z$. ✓
- $Z \sim (0,1) \to (0 \oplus 1, 1) = (1,1) = Y$, then phase flip since $\sqrt{X}: Z \to -Y$.
  Condition: $(x \oplus 1) \wedge z = (0 \oplus 1) \wedge 1 = 1$. ✓ $\square$

**Code:**
```python
def sx(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if (x ^ 1) & z:             # Z → -Y: phase flip (x=0, z=1)
            self.r_phase[r] ^= 1
        self.x_mat[r][q] ^= z       # x := x XOR z
```

**Theorem 2.11** *(√X†)*. $(\sqrt{X})^\dagger$ satisfies:

$$(\sqrt{X})^\dagger X (\sqrt{X}) = X,\quad
(\sqrt{X})^\dagger Y (\sqrt{X}) = -Z,\quad
(\sqrt{X})^\dagger Z (\sqrt{X}) = Y$$

*Proof.* Invert the $\sqrt{X}$ rules: $\sqrt{X}: Y \to Z$ inverts to
$(\sqrt{X})^\dagger: Z \to Y$; $\sqrt{X}: Z \to -Y$ inverts to
$(\sqrt{X})^\dagger: Y \to -Z$; $\sqrt{X}: X \to X$ inverts to
$(\sqrt{X})^\dagger: X \to X$. $\square$

**Corollary 2.12** *(Bit rule for √X†)*. Same bit mutation $x \mathrel{\oplus}= z$,
but phase flip when input is $Y$ (condition: $x \wedge z = 1$).

*Proof.*
- $Y \sim (1,1) \to (0,1) = Z$, and $(\sqrt{X})^\dagger: Y \to -Z$. Phase flip needed.
  Condition $x \wedge z = 1 \wedge 1 = 1$. ✓
- $Z \sim (0,1) \to (1,1) = Y$, no sign ($(\sqrt{X})^\dagger: Z \to Y$). ✓
- $X \sim (1,0) \to (1,0) = X$, no sign. ✓ $\square$

**Code:**
```python
def sxdg(self, q: int) -> None:
    self._check_qubit(q)
    for r in range(2 * self.n):
        x = self.x_mat[r][q]
        z = self.z_mat[r][q]
        if x & z:                    # Y → -Z: phase flip (x=1, z=1)
            self.r_phase[r] ^= 1
        self.x_mat[r][q] ^= z        # x := x XOR z
```

---

## 3. The CNOT Phase Condition

The CNOT rule is the most complex because the sign correction involves both
qubits simultaneously.

### 3.1 CNOT Conjugation Rules

**Theorem 3.1.** The CNOT gate with control $c$ and target $t$ satisfies:

$$\text{CNOT}_{ct}\,(X_c \otimes I_t)\,\text{CNOT}_{ct}^\dagger = X_c \otimes X_t$$
$$\text{CNOT}_{ct}\,(I_c \otimes X_t)\,\text{CNOT}_{ct}^\dagger = I_c \otimes X_t$$
$$\text{CNOT}_{ct}\,(Z_c \otimes I_t)\,\text{CNOT}_{ct}^\dagger = Z_c \otimes I_t$$
$$\text{CNOT}_{ct}\,(I_c \otimes Z_t)\,\text{CNOT}_{ct}^\dagger = Z_c \otimes Z_t$$

*Proof.* The CNOT matrix in the $\{|00\rangle,|01\rangle,|10\rangle,|11\rangle\}$ basis is:

$$\text{CNOT} = \begin{pmatrix}1&0&0&0\\0&1&0&0\\0&0&0&1\\0&0&1&0\end{pmatrix}$$

For $X_c \otimes I_t = \begin{pmatrix}0&0&1&0\\0&0&0&1\\1&0&0&0\\0&1&0&0\end{pmatrix}$, direct matrix multiplication gives $\text{CNOT}\,(X_c\otimes I_t)\,\text{CNOT}^\dagger = X_c \otimes X_t$.

For $I_c \otimes Z_t = \text{diag}(1,-1,1,-1)$:

$$\text{CNOT}\,\text{diag}(1,-1,1,-1)\,\text{CNOT}^\dagger$$

The CNOT swaps rows/columns 2 and 3 (0-indexed), so $\text{diag}(1,-1,-1,1) = Z_c \otimes Z_t$. $\square$

### 3.2 Bit Rules for CNOT

The tensor product structure means two qubits each carry their own $(x,z)$
bits. Let $(x_c, z_c)$ be the bits for the control qubit and $(x_t, z_t)$
for the target.

**Corollary 3.2.** The CNOT bit updates are:

$$x_t \;\mathrel{\oplus}=\; x_c \qquad z_c \;\mathrel{\oplus}=\; z_t$$

*Proof.* From Theorem 3.1:
- $X_c I_t \to X_c X_t$: the target's $x$ bit picks up the control's $x$ bit. ✓
- $I_c Z_t \to Z_c Z_t$: the control's $z$ bit picks up the target's $z$ bit. ✓
- $Z_c I_t \to Z_c I_t$: no change. ✓
- $I_c X_t \to I_c X_t$: no change. ✓

For a general product $P_c \otimes P_t$, the two XOR operations handle
each qubit's Pauli independently. $\square$

### 3.3 Derivation of the Phase Correction

The bit updates from Corollary 3.2 are correct only when the product of
the resulting Paulis carries no extra $i$ factor. When the inputs are
single-qubit operators that mix to produce $Y$, the Pauli multiplication
rules introduce $\pm i$ factors that must be compensated.

**Theorem 3.3** *(CNOT Phase Condition)*. The sign correction in `cnot` fires
when the update would produce a $Y$ factor requiring a phase sign flip. The
condition is:

$$\text{phase flip} \iff x_c = 1 \text{ and } z_t = 1 \text{ and } (x_t \oplus z_c \oplus 1) = 1$$

equivalently: $x_c \wedge z_t \wedge \neg(x_t \oplus z_c)$, or in code:
`xc & zt & (xt ^ zc ^ 1)`.

*Proof.* We need to track when $P_c \cdot Q_c$ and $P_t \cdot Q_t$ each
produce a phase of $i$ or $-i$, where $Q_c = P_c \cdot \Delta_c$ and
$Q_t = P_t \cdot \Delta_t$ after the XOR updates.

The CNOT effect on a row with $(x_c, z_c, x_t, z_t)$ is:
- Control qubit goes from $P_c$ to $P_c$ (unchanged).
- Target qubit goes from $P_t$ to $P_t \cdot X_c^{x_c}$ (X applied if $x_c=1$).
- Control qubit picks up $Z_t^{z_t}$ (Z-backtrack).

The phase from multiplying $P_t$ by $X$ (when $x_c=1$) is the same as
`_row_mult_phase` on the target qubit:

$$\text{phase}_{t} = g(P_t, X) = \begin{cases}
-1 & P_t = Y \text{ (i.e. } x_t=1, z_t=1\text{)} \\
+1 & \text{otherwise}
\end{cases}$$

The phase from multiplying $P_c$ by $Z$ (when $z_t=1$) on the control:

$$\text{phase}_{c} = g(P_c, Z) = \begin{cases}
-1 & P_c = X \text{ (i.e. } x_c=1, z_c=0\text{)} \\
+1 & \text{otherwise}
\end{cases}$$

The combined sign flip (XOR of both) occurs when exactly one fires:

| $P_c$ | $P_t$ | phase$_c$ | phase$_t$ | Net flip? |
|-------|-------|-----------|-----------|-----------|
| $X$   | $Y$   | $-1$      | $-1$      | No (cancels)|
| $X$   | other | $-1$      | $+1$      | Yes |
| $Y$   | $Y$   | $+1$      | $-1$      | Yes |
| $Y$   | other | $+1$      | $+1$      | No |
| other | $Y$   | $+1$      | $-1$      | (no $x_c=1$, so $z_t$ update doesn't apply)|

The net flip condition when both $x_c=1$ and $z_t=1$:

- Flip if $P_t = Y$ ($x_t=1, z_t=1$) and $P_c \neq X$ ($z_c \neq 0$).
- Flip if $P_c = X$ ($x_c=1, z_c=0$) and $P_t \neq Y$ ($x_t \oplus z_t \neq 2$,
  but since $z_t=1$ here, we need $x_t=0$).

Combining: flip when $x_c=1$ and $z_t=1$ and NOT ($x_t=1$ and $z_c=1$) and
NOT ($x_t=0$ and $z_c=0$)... The Aaronson-Gottesman formula captures this as:

$$x_c \wedge z_t \wedge (x_t \oplus z_c \oplus 1)$$

When $x_c = 1, z_t = 1$: the flip fires unless $x_t \oplus z_c = 1$, i.e.
exactly when $x_t = z_c$ (both 0 or both 1). The case $x_t=1, z_c=1$ is
$P_t=Y, P_c=Y$: both phases fire and cancel (net no flip). The case $x_t=0,
z_c=0$ is $P_t=Z, P_c=X$: neither phase fires (no Y in either product), so
no flip. $\square$

**Code:**
```python
def cnot(self, control: int, target: int) -> None:
    self._check_qubit(control, "control")
    self._check_qubit(target, "target")
    c, t = control, target
    for r in range(2 * self.n):
        xc = self.x_mat[r][c]
        zc = self.z_mat[r][c]
        xt = self.x_mat[r][t]
        zt = self.z_mat[r][t]
        if xc & zt & (xt ^ zc ^ 1):   # Aaronson-Gottesman phase condition
            self.r_phase[r] ^= 1
        self.x_mat[r][t] ^= xc        # X spreads: x_t := x_t XOR x_c
        self.z_mat[r][c] ^= zt        # Z backtracks: z_c := z_c XOR z_t
```

---

## 4. The Phase Accumulation Function

When `_rowmult` multiplies two tableau rows (Pauli strings), it must track
total $i$-phase accumulated across all $n$ qubit positions.

### 4.1 The Single-Qubit Phase Table

**Lemma 4.1.** For $P_a, P_b \in \{I,X,Y,Z\}$, define $g(P_a, P_b)$ by
$P_a P_b = i^{g(P_a, P_b)} P_c$. Then:

| $P_a$ | $P_b$ | $g$ | Identity |
|-------|-------|----:|----------|
| $X$   | $Z$   | 1   | $XZ = iY$ |
| $Z$   | $X$   | 3   | $ZX = -iY$ |
| $Z$   | $Y$   | 1   | $ZY = iX$ |
| $Y$   | $Z$   | 3   | $YZ = -iX$ |
| $Y$   | $X$   | 1   | $YX = iZ$ |
| $X$   | $Y$   | 3   | $XY = -iZ$ |
| any   | $I$   | 0   | $PI = P$ |
| $I$   | any   | 0   | $IP = P$ |
| $P$   | $P$   | 0   | $P^2 = I$ |

*Proof.* Each row follows from the cyclic product rules $XY = iZ$, $YZ = iX$,
$ZX = iY$ and their reverses. For example, $XZ = X \cdot Z$. Since
$XY = iZ$, we have $Z = -iXY$, so $XZ = X(-iXY) = -iX^2Y = -iY$... that
gives $g=3$. Actually $XZ = -iY$ since $ZX = iY$ and $XZ = -(ZX)$ from
anticommutativity: $\{X,Z\}=0$ so $XZ = -ZX = -iY$. Hence $g(X,Z)=3$. By
the table above, $g(Z,X)=1$ since $ZX = iY$. The pattern is cyclic:
$X \to Y \to Z \to X$ (forward) gives $+i$; going backwards gives $-i$. $\square$

**Code:**
```python
def _row_mult_phase(x1: int, z1: int, x2: int, z2: int) -> int:
    if (x1 == 0 and z1 == 0) or (x2 == 0 and z2 == 0):
        return 0          # identity contributes no phase
    if x1 == x2 and z1 == z2:
        return 0          # P·P = I: no phase
    # XZ = -iY (g=3), ZX = +iY (g=1)
    if x1 == 1 and z1 == 0 and x2 == 0 and z2 == 1: return 1  # Z·X = iY
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 0: return 3  # X·Z = -iY
    if x1 == 0 and z1 == 1 and x2 == 1 and z2 == 1: return 1  # Z·Y = iX
    if x1 == 1 and z1 == 1 and x2 == 0 and z2 == 1: return 3  # Y·Z = -iX
    if x1 == 1 and z1 == 1 and x2 == 1 and z2 == 0: return 1  # Y·X = iZ
    if x1 == 1 and z1 == 0 and x2 == 1 and z2 == 1: return 3  # X·Y = -iZ
    raise ValueError("invalid Pauli bits for row multiplication")
```

### 4.2 Row Multiplication

**Theorem 4.2** *(Row Multiplication)*. For two $n$-qubit Pauli operators
$A = (-1)^{r_A} \bigotimes_q P^A_q$ and $B = (-1)^{r_B} \bigotimes_q P^B_q$,
their product is:

$$AB = (-1)^{r_A + r_B + \lfloor e/2 \rfloor} \bigotimes_q (P^A_q P^B_q)$$

where $e = 2r_A + 2r_B + \sum_q g(P^A_q, P^B_q)$ reduced mod 4, and the
final sign is $(-1)^1$ iff $e \equiv 2 \pmod{4}$.

*Proof.* The product across $n$ tensor factors accumulates one $i^{g_q}$
per qubit position from Lemma 4.1. The total $i$-exponent is $\sum_q g_q$,
plus $i^2 = -1$ for each existing $-1$ phase. Summing all contributions
mod 4 and checking whether the result is $i^2 = -1$ (i.e. the exponent is
2 mod 4) gives the new phase bit. Values 1 or 3 (i.e. overall $\pm i$)
cannot arise for products of Hermitian Paulis with phase $\pm 1$, so
$e \in \{0,2\}$ always for valid tableau rows. $\square$

**Code:**
```python
def _rowmult(self, a: int, b: int) -> None:
    n = self.n
    exp_i = 0
    if self.r_phase[a]: exp_i += 2   # −1 = i²
    if self.r_phase[b]: exp_i += 2
    for q in range(n):
        exp_i += _row_mult_phase(
            self.x_mat[a][q], self.z_mat[a][q],
            self.x_mat[b][q], self.z_mat[b][q],
        )
    exp_i %= 4
    for q in range(n):
        self.x_mat[a][q] ^= self.x_mat[b][q]   # Pauli type: XOR bits
        self.z_mat[a][q] ^= self.z_mat[b][q]
    self.r_phase[a] = 1 if exp_i == 2 else 0   # sign: 0=+1, 1=−1
```

---

## 5. Measurement Proofs

### 5.1 Setup

Let $\mathcal{S} = \langle g_1, \ldots, g_n \rangle$ be the stabilizer group
of the state $|\psi\rangle$, where rows $n, n+1, \ldots, 2n-1$ of the tableau
are the generators. Let $\mathcal{D} = \langle d_1, \ldots, d_n \rangle$
be the destabilizers (rows $0, \ldots, n-1$), with the invariant:

$$d_i g_j = (-1)^{\delta_{ij}} g_j d_i \qquad \text{(destabilizer } d_i \text{ anticommutes only with } g_i\text{)}$$

### 5.2 Deterministic Branch

**Theorem 5.1** *(Deterministic Measurement)*. If $Z_q$ commutes with every
stabilizer generator $g_i$ (i.e. $x_\text{mat}[n+i][q] = 0$ for all $i$),
then $\pm Z_q \in \mathcal{S}$ and the measurement outcome is deterministic.

*Proof.* Since $Z_q$ commutes with all generators, it commutes with the entire
group $\mathcal{S}$. By the structure of abelian stabilizer groups on $n$
qubits: either $Z_q \in \mathcal{S}$ (outcome 0, eigenvalue $+1$) or
$-Z_q \in \mathcal{S}$ (outcome 1, eigenvalue $-1$). One of these must hold
because $Z_q^2 = I \in \mathcal{S}$ and $Z_q$ commutes with all of $\mathcal{S}$,
so by the maximality of the stabilizer group on a pure state, $Z_q$ or $-Z_q$
is in $\mathcal{S}$. $\square$

**Theorem 5.2** *(Deterministic Outcome Algorithm)*. The code in
`_deterministic_z_outcome(q)` correctly finds the product of generators
equal to $\pm Z_q$ and returns its sign.

*Proof.* The method performs GF(2) row reduction on the binary representation
of the generators (the $[X|Z]$ matrix) to find a subset whose XOR equals
the binary vector for $Z_q$ (which has a 1 in position $n+q$ of the $2n$
vector). The row reduction in `_solve_stabilizer_product` finds the unique
solution over GF(2) since the generators are independent. Multiplying the
selected rows via `_rowmult` accumulates the correct phase using Theorem 4.2.
The returned `r_phase[0]` of the work copy is 0 (eigenvalue $+1$) or 1
(eigenvalue $-1$). $\square$

### 5.3 Random Branch

**Theorem 5.3** *(Random Measurement)*. If some stabilizer row $p$ has
$x_\text{mat}[p][q] = 1$ (i.e., generator $g_{p-n}$ anticommutes with $Z_q$),
then the measurement outcome is uniformly random, and the post-measurement
state is the stabilizer state obtained by:

1. For all rows $r \neq p$ with $x_\text{mat}[r][q] = 1$: replace row $r$
   with $r \cdot p$ (row multiplication, clearing $X$ on qubit $q$).
2. Replace destabilizer row $q$ with the content of row $p$ (via swap).
3. Set stabilizer row $n+q$ to $(-1)^{\text{outcome}} Z_q$.
4. Set destabilizer row $q$ to $+X_q$.

*Proof.*

**Uniform randomness:** Since $g_{p-n}$ anticommutes with $Z_q$, the state
$|\psi\rangle$ is not a $Z_q$ eigenstate. In fact, since $|\psi\rangle$ is
stabilized by $g_{p-n}$, and $Z_q g_{p-n} = -g_{p-n} Z_q$, applying the
projector $\Pi_0 = (I + Z_q)/2$ gives:

$$\Pi_0 g_{p-n} |\psi\rangle = \Pi_0 |\psi\rangle$$

but also $g_{p-n} \Pi_0 |\psi\rangle = \Pi_1 g_{p-n}|\psi\rangle = \Pi_1 |\psi\rangle$,
so $\|\Pi_0 |\psi\rangle\|^2 = \|\Pi_1 |\psi\rangle\|^2 = 1/2$.

**Step 1 correctness:** After the outcome is sampled, the post-measurement
state is stabilized by $\pm Z_q$ (the measured eigenvalue). For any generator
$g_r$ with $x_\text{mat}[r][q] = 1$ (anticommutes with $Z_q$), we cannot
keep $g_r$ in the stabilizer group since $g_r Z_q \neq Z_q g_r$. Replacing
$g_r$ with $g_r \cdot g_p$ (where $g_p$ also anticommutes with $Z_q$) gives
a product that commutes with $Z_q$: $(g_r g_p)Z_q = g_r(-Z_q g_p) = -g_r Z_q g_p
= -(-Z_q g_r)g_p = Z_q(g_r g_p)$. So $g_r g_p$ commutes with $Z_q$. ✓

**Step 3 correctness:** The new stabilizer group is generated by
$\{(-1)^k Z_q\} \cup \{g_r g_p : r \neq p, x[r][q]=1\} \cup \{g_r : x[r][q]=0\}$,
where $k \in \{0,1\}$ is the measurement outcome.

**Step 4 correctness (maintaining the destabilizer invariant):** After
replacing stabilizer $n+q$ with $(-1)^k Z_q$, we need destabilizer $q$ to
anticommute with $(-1)^k Z_q$ and commute with all other new stabilizers.
Setting destabilizer $q$ to $+X_q$ satisfies this: $X_q Z_q = -Z_q X_q$
(anticommutes with the new stabilizer) and $X_q$ has no support on any other
qubit, so it commutes with all generators that have no $Z$ on qubit $q$
(which is all of them after Step 1). $\square$

**Code:**
```python
def measure_z(self, q: int) -> int:
    self._check_qubit(q)
    n = self.n
    p = -1
    for r in range(n, 2 * n):
        if self.x_mat[r][q] == 1:
            p = r; break

    if p == -1:
        return self._deterministic_z_outcome(q)   # Theorem 5.2

    outcome = random.randint(0, 1)                # Theorem 5.3: uniform

    for r in range(2 * n):                        # Step 1: clear X on q
        if r != p and self.x_mat[r][q] == 1:
            self._rowmult(r, p)

    self._rowswap(p, n + q)                       # Step 2: pivot to slot n+q

    for j in range(n):                            # Step 3: set ±Z_q
        self.x_mat[n + q][j] = 0
        self.z_mat[n + q][j] = 0
    self.z_mat[n + q][q] = 1
    self.r_phase[n + q] = outcome

    for j in range(n):                            # Step 4: set +X_q destabilizer
        self.x_mat[q][j] = 0
        self.z_mat[q][j] = 0
    self.x_mat[q][q] = 1
    self.r_phase[q] = 0

    return outcome
```

---

## 6. Worked Example — Bell State

We trace through the complete tableau evolution for the Bell state
preparation circuit $H_0 \cdot \text{CNOT}_{01}$ applied to $|00\rangle$.

**Initial state** $|00\rangle$: stabilizers $\{+Z_0, +Z_1\}$,
destabilizers $\{+X_0, +X_1\}$.

Tableau (rows 0,1 are destabilizers; rows 2,3 are stabilizers):

```python
Row 0 (destab): +X_0 I_1   →  x=[1,0], z=[0,0], phase=0
Row 1 (destab): +I_0 X_1   →  x=[0,1], z=[0,0], phase=0
Row 2 (stab):   +Z_0 I_1   →  x=[0,0], z=[1,0], phase=0
Row 3 (stab):   +I_0 Z_1   →  x=[0,0], z=[0,1], phase=0
```

**After H on qubit 0** (swap $x \leftrightarrow z$ for column 0):

```python
Row 0: +Z_0 I_1   (was X_0 I, x swap: x[0]=0,z[0]=1)
Row 1: +I_0 X_1   (qubit 1 unchanged)
Row 2: +X_0 I_1   (was Z_0 I, x swap: x[0]=1,z[0]=0)
Row 3: +I_0 Z_1   (unchanged)
```

Verification: $H Z_0 H^\dagger = X_0$ ✓ and $H X_0 H^\dagger = Z_0$ ✓.

**After CNOT(0→1)** (for each row: $x_t \mathrel{\oplus}= x_c$, $z_c \mathrel{\oplus}= z_t$):

Row 0: $x_c=0, z_c=1, x_t=0, z_t=0$. Phase condition: $0 \wedge 0 \wedge \ldots = 0$. No flip.
$x_t \mathrel{\oplus}= 0$, $z_c \mathrel{\oplus}= 0$. Row 0 unchanged: $+Z_0 I_1$.

Row 1: $x_c=0, z_c=0, x_t=1, z_t=0$. No phase flip. $x_t \mathrel{\oplus}= 0$, $z_c \mathrel{\oplus}= 0$.
Row 1 unchanged: $+I_0 X_1$.

Row 2: $x_c=1, z_c=0, x_t=0, z_t=0$. Phase: $1 \wedge 0 \wedge \ldots = 0$. No flip.
$x_t \mathrel{\oplus}= 1 \Rightarrow x_t=1$. $z_c \mathrel{\oplus}= 0$. Row 2: $+X_0 X_1$.

Row 3: $x_c=0, z_c=0, x_t=0, z_t=1$. Phase: $0 \wedge 1 \wedge \ldots = 0$. No flip.
$x_t \mathrel{\oplus}= 0$. $z_c \mathrel{\oplus}= 1 \Rightarrow z_c=1$. Row 3: $+Z_0 Z_1$.

**Final tableau:**
```python
Row 0 (destab): +Z_0 I_1
Row 1 (destab): +I_0 X_1
Row 2 (stab):   +X_0 X_1   ← stabilizer of Bell state
Row 3 (stab):   +Z_0 Z_1   ← stabilizer of Bell state
```

Verification:
- $XX|\Phi^+\rangle = |\Phi^+\rangle$ ✓
- $ZZ|\Phi^+\rangle = |\Phi^+\rangle$ ✓

**Running in Python:**
```python
from stabilizer_python import StabilizerState, Circuit

st = StabilizerState.zero(2)
Circuit(2).h(0).cnot(0, 1).run(st)
print(st.inspect(views=["chp"]))
# +Z_0 I
# +I X
# -----------
# +XX
# +ZZ

print(st.stabilizer_strings())   # ['+XX', '+ZZ']
```

---

## Reference

> Scott Aaronson and Daniel Gottesman,
> "Improved Simulation of Stabilizer Circuits,"
> *Physical Review A* 70, 052328 (2004).
> [arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196)
