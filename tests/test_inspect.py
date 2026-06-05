import pytest

from stabilizer_python import Circuit, StabilizerState


def _bell_state() -> StabilizerState:
    st = StabilizerState.zero(2)
    Circuit(2).h(0).cnot(0, 1).run(st)
    return st


def test_inspect_default_includes_all_four_views():
    text = _bell_state().inspect()
    assert "+XX" in text
    assert "+ZZ" in text
    assert "X matrix (4 x 2)" in text
    assert "Phase matrix (4 x 1)" in text
    assert "Tableau (CHP-style destabilizers | stabilizers):" in text


def test_inspect_selective_stabilizer_and_destabilizer_rows():
    st = _bell_state()
    text = st.inspect(views=["stabilizers", "destabilizers"])
    assert text == st._format_stabilizers_only() + "\n\n" + st._format_destabilizers_only()


def test_inspect_selective_chp_binary_phase():
    st = _bell_state()
    text = st.inspect(views=["chp", "binary", "phase"])
    assert text == (
        st.format_chp_printstate()
        + "\n\n"
        + st.format_xz_binary_matrices()
        + "\n\n"
        + st.format_phase_matrix()
    )


def test_inspect_unknown_view_raises():
    with pytest.raises(ValueError, match="unknown inspect view"):
        StabilizerState.zero(1).inspect(views=["chp", "not-a-view"])
