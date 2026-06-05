"""Tests for StabilizerState inspection API."""
from stabilizer_python import Circuit, StabilizerState


def _ghz3() -> StabilizerState:
    st = StabilizerState.zero(3)
    Circuit(3).h(0).cnot(0, 1).cnot(0, 2).run(st)
    return st


def _bell() -> StabilizerState:
    st = StabilizerState.zero(2)
    Circuit(2).h(0).cnot(0, 1).run(st)
    return st


# --- inspect() default ---

def test_inspect_default_shows_chp_only():
    st = _bell()
    out = st.inspect()
    # Must contain the separator and Pauli strings
    assert "---" in out or "----" in out
    assert "+XX" in out
    assert "+ZZ" in out
    # Must NOT contain 'X matrix' or 'Phase matrix' (binary/phase views)
    assert "X matrix" not in out
    assert "Phase matrix" not in out


def test_inspect_explicit_views():
    st = _bell()
    out = st.inspect(views=["binary", "phase"])
    assert "X matrix" in out
    assert "Phase matrix" in out
    assert "+XX" not in out  # chp view not requested


def test_inspect_unknown_view_raises():
    st = _bell()
    try:
        st.inspect(views=["not-a-view"])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


# --- stabilizer_strings() ---

def test_stabilizer_strings_bell():
    st = _bell()
    labels = st.stabilizer_strings()
    assert isinstance(labels, list)
    assert len(labels) == 2
    assert "+XX" in labels
    assert "+ZZ" in labels


def test_stabilizer_strings_ghz3():
    st = _ghz3()
    labels = st.stabilizer_strings()
    assert len(labels) == 3
    assert "+XXX" in labels
    assert "+ZZI" in labels
    assert "+ZIZ" in labels


def test_stabilizer_strings_zero_state():
    st = StabilizerState.zero(2)
    labels = st.stabilizer_strings()
    assert "+ZI" in labels
    assert "+IZ" in labels


# --- destabilizer_strings() ---

def test_destabilizer_strings_returns_list():
    st = _bell()
    labels = st.destabilizer_strings()
    assert isinstance(labels, list)
    assert len(labels) == 2
    for s in labels:
        assert s[0] in ('+', '-')
        assert len(s) == 3  # sign + 2 Pauli chars


def test_destabilizer_strings_zero_state():
    st = StabilizerState.zero(2)
    labels = st.destabilizer_strings()
    assert "+XI" in labels
    assert "+IX" in labels


# --- from_stabilizer_list() ---

def test_from_stabilizer_list_bell():
    st = StabilizerState.from_stabilizer_list(["+XX", "+ZZ"])
    labels = st.stabilizer_strings()
    assert "+XX" in labels
    assert "+ZZ" in labels


def test_from_stabilizer_list_no_sign_prefix():
    # Signs are optional; bare strings default to +
    st = StabilizerState.from_stabilizer_list(["XX", "ZZ"])
    labels = st.stabilizer_strings()
    assert "+XX" in labels
    assert "+ZZ" in labels


def test_from_stabilizer_list_negative_sign():
    st = StabilizerState.from_stabilizer_list(["-ZI", "+IZ"])
    labels = st.stabilizer_strings()
    assert "-ZI" in labels
    assert "+IZ" in labels


def test_from_stabilizer_list_zero_state():
    st = StabilizerState.from_stabilizer_list(["ZI", "IZ"])
    labels = st.stabilizer_strings()
    assert "+ZI" in labels
    assert "+IZ" in labels


def test_from_stabilizer_list_invalid_char_raises():
    try:
        StabilizerState.from_stabilizer_list(["XA"])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_from_stabilizer_list_wrong_count_raises():
    try:
        StabilizerState.from_stabilizer_list(["+XX"])  # 2-qubit op but only 1 generator
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_from_stabilizer_list_roundtrip():
    # Build a state, read its stabilizers, reconstruct, compare stabilizers.
    original = _ghz3()
    labels = original.stabilizer_strings()
    reconstructed = StabilizerState.from_stabilizer_list(labels)
    assert set(reconstructed.stabilizer_strings()) == set(labels)
