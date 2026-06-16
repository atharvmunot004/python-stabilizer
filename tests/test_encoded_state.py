"""
Tests for EncodedState -- logical operator tracking.
"""
import pytest

from stabilizer_python import EncodedState, StabilizerState
from stabilizer_python.stabilizer_code import BitFlip3Code, PerfectCode, SteaneCode


def test_construction_from_code():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert enc.k == 1
    assert len(enc.logical_xs) == 1
    assert len(enc.logical_zs) == 1
    assert enc.physical is state


def test_construction_from_logical_ops():
    state = BitFlip3Code.zero_state()
    enc = EncodedState.from_logical_ops(
        state,
        logical_xs=["+XXX"],
        logical_zs=["+IIZ"],
        check_operators=["ZZI", "IZZ"],
    )
    assert enc.k == 1
    assert enc.logical_xs == ["+XXX"]
    assert enc.logical_zs == ["+IIZ"]


def test_construction_mismatched_logical_ops_raises():
    state = StabilizerState.zero(3)
    with pytest.raises(ValueError):
        EncodedState.from_logical_ops(
            state, logical_xs=["+XXX", "+ZZZ"], logical_zs=["+IIZ"]
        )


def test_out_of_range_logical_qubit_raises():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    with pytest.raises(IndexError):
        enc.logical_z_eigenvalue(1)


def test_logical_z_eigenvalue_zero_logical_is_plus1():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert enc.logical_z_eigenvalue(0) == +1


def test_measure_logical_z_zero_logical_returns_0():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert enc.measure_logical_z(0) == 0


def test_apply_logical_x_flips_logical_z_eigenvalue():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_x(0)
    assert enc.logical_z_eigenvalue(0) == -1


def test_apply_logical_x_is_tracked_not_error():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_x(0)
    assert not enc.has_logical_error()
    assert enc.logical_error_type(0) == "I"


def test_measure_logical_z_after_logical_x_returns_1():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_x(0)
    assert enc.measure_logical_z(0) == 1


def test_double_logical_x_restores_zero():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_x(0)
    enc.apply_logical_x(0)
    assert enc.logical_z_eigenvalue(0) == +1
    assert not enc.has_logical_error()


def test_apply_logical_z_does_not_change_logical_z_eigenvalue():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_z(0)
    assert enc.logical_z_eigenvalue(0) == +1


def test_no_logical_error_after_clean_encoding():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert not enc.has_logical_error()
    assert enc.logical_error_type(0) == "I"


def test_no_logical_error_perfect_code():
    state = PerfectCode.zero_state()
    enc = EncodedState(state, PerfectCode)
    assert not enc.has_logical_error()


def test_no_logical_error_steane_code():
    state = SteaneCode.zero_state()
    enc = EncodedState(state, SteaneCode)
    assert not enc.has_logical_error()


def test_correctable_x_error_no_logical_error_after_correction():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)

    enc.physical.x(0)

    from stabilizer_python import read_syndrome

    syndrome = read_syndrome(enc.physical, ["ZZI", "IZZ"])
    if syndrome == [1, 0]:
        enc.physical.x(0)
    elif syndrome == [1, 1]:
        enc.physical.x(1)
    elif syndrome == [0, 1]:
        enc.physical.x(2)

    assert not enc.has_logical_error()


def test_uncorrectable_triple_x_error_is_detected():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)

    enc.physical.x(0)
    enc.physical.x(1)
    enc.physical.x(2)

    assert enc.has_logical_x_error(0)
    assert enc.logical_error_type(0) == "X"


def test_logical_x_error_detected_for_perfect_code():
    state = PerfectCode.zero_state()
    enc = EncodedState(state, PerfectCode)

    for q in range(5):
        enc.physical.x(q)

    assert enc.logical_z_eigenvalue(0) == -1
    assert enc.has_logical_x_error(0)


def test_valid_codeword_after_encoding():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert enc.is_valid_codeword()


def test_invalid_codeword_after_single_error():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.physical.x(1)
    assert not enc.is_valid_codeword()
    assert enc.syndrome() == [1, 1]


def test_syndrome_empty_when_no_checks():
    state = StabilizerState.zero(3)
    enc = EncodedState.from_logical_ops(
        state, logical_xs=["+XXX"], logical_zs=["+IIZ"]
    )
    assert enc.syndrome() == []
    assert enc.is_valid_codeword()


def test_logical_state_string_zero():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert enc.logical_state_string(0) == "|0_L>"


def test_logical_state_string_one_after_logical_x():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_x(0)
    assert enc.logical_state_string(0) == "|1_L>"


def test_summary_contains_code_name():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code, code_name="BitFlip3")
    out = enc.summary()
    assert "BitFlip3" in out
    assert "Xbar" in out


def test_repr_contains_state_label():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    assert "|0_L>" in repr(enc)


def test_apply_logical_y_changes_state():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    enc.apply_logical_y(0)
    assert enc.logical_z_eigenvalue(0) == -1
    assert not enc.has_logical_error()


def test_from_logical_ops_syndrome_works():
    state = BitFlip3Code.zero_state()
    state.x(2)

    enc = EncodedState.from_logical_ops(
        state,
        logical_xs=["+XXX"],
        logical_zs=["+IIZ"],
        check_operators=["ZZI", "IZZ"],
    )
    assert enc.syndrome() == [0, 1]
    assert not enc.is_valid_codeword()


def test_measure_logical_x_undetermined_raises_for_zero_state():
    state = BitFlip3Code.zero_state()
    enc = EncodedState(state, BitFlip3Code)
    with pytest.raises(ValueError):
        enc.measure_logical_x(0)
