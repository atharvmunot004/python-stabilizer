"""Tests for the general StabilizerCode class and named code instances."""
import pytest

from stabilizer_python import (
    BitFlip3Code,
    PerfectCode,
    StabilizerCode,
    SteaneCode,
    SurfaceCode3,
)
from stabilizer_python.stabilizer_code import PhaseFlip3Code, _gf2_row_reduce, _parse_pauli


def test_wrong_generator_count_raises():
    with pytest.raises(ValueError):
        StabilizerCode(n=3, k=1, generators=["+ZZI"])


def test_anticommuting_generators_raises():
    with pytest.raises(ValueError):
        StabilizerCode(n=2, k=0, generators=["+XX", "+ZI"])


def test_wrong_generator_length_raises():
    with pytest.raises(ValueError):
        StabilizerCode(n=3, k=1, generators=["+ZZ", "+IZZ"])


def test_dependent_generators_raise():
    with pytest.raises(ValueError):
        StabilizerCode(n=3, k=1, generators=["+ZZI", "+ZZI"])


def test_repr_and_str():
    code = BitFlip3Code
    assert "3" in repr(code)
    text = str(code)
    assert "Bit-flip" in text or "[[3, 1]]" in text or "ZZI" in text


def test_bitflip3_parameters():
    assert BitFlip3Code.n == 3
    assert BitFlip3Code.k == 1
    assert len(BitFlip3Code.generators) == 2


def test_bitflip3_encode():
    state = BitFlip3Code.zero_state()
    assert state.n == 3
    stabs = state.stabilizer_strings()
    assert any("ZZI" in s for s in stabs)
    assert any("IZZ" in s for s in stabs)


def test_bitflip3_syndrome_no_error():
    state = BitFlip3Code.zero_state()
    assert BitFlip3Code.read_syndrome(state) == [0, 0]


def test_bitflip3_syndrome_x_error_q0():
    state = BitFlip3Code.zero_state()
    state.x(0)
    assert BitFlip3Code.read_syndrome(state) == [1, 0]


def test_bitflip3_syndrome_x_error_q1():
    state = BitFlip3Code.zero_state()
    state.x(1)
    assert BitFlip3Code.read_syndrome(state) == [1, 1]


def test_bitflip3_syndrome_x_error_q2():
    state = BitFlip3Code.zero_state()
    state.x(2)
    assert BitFlip3Code.read_syndrome(state) == [0, 1]


def test_bitflip3_n_unchanged_after_syndrome():
    state = BitFlip3Code.zero_state()
    n_before = state.n
    BitFlip3Code.read_syndrome(state)
    assert state.n == n_before


def test_bitflip3_logical_operators():
    lx = BitFlip3Code.logical_x(0)
    lz = BitFlip3Code.logical_z(0)
    assert len(lx.lstrip("+-")) == 3
    assert len(lz.lstrip("+-")) == 3


def test_phaseflip_named_code():
    state = PhaseFlip3Code.zero_state()
    assert PhaseFlip3Code.read_syndrome(state) == [0, 0]
    state.z(1)
    assert PhaseFlip3Code.read_syndrome(state) == [1, 1]


def test_perfect_code_parameters():
    assert PerfectCode.n == 5
    assert PerfectCode.k == 1
    assert len(PerfectCode.generators) == 4


def test_perfect_code_generators_commute():
    code = StabilizerCode(
        n=5,
        k=1,
        generators=["+XZZXI", "+IXZZX", "+XIXZZ", "+ZXIXZ"],
    )
    assert code.n == 5


def test_perfect_code_syndrome_no_error():
    state = PerfectCode.zero_state()
    assert PerfectCode.read_syndrome(state) == [0, 0, 0, 0]


def test_perfect_code_syndrome_x_error():
    state = PerfectCode.zero_state()
    state.x(2)
    assert PerfectCode.read_syndrome(state) != [0, 0, 0, 0]


def test_perfect_code_logical_operators():
    lx = PerfectCode.logical_x(0)
    lz = PerfectCode.logical_z(0)
    assert len(lx.lstrip("+-")) == 5
    assert len(lz.lstrip("+-")) == 5


def test_perfect_code_distance():
    assert PerfectCode.distance() == 3


def test_steane_parameters():
    assert SteaneCode.n == 7
    assert SteaneCode.k == 1
    assert len(SteaneCode.generators) == 6


def test_steane_syndrome_no_error():
    state = SteaneCode.zero_state()
    assert SteaneCode.read_syndrome(state) == [0, 0, 0, 0, 0, 0]


def test_steane_syndrome_detects_x_error():
    state = SteaneCode.zero_state()
    state.x(0)
    assert any(s == 1 for s in SteaneCode.read_syndrome(state))


def test_steane_syndrome_detects_z_error():
    state = SteaneCode.zero_state()
    state.z(3)
    assert any(s == 1 for s in SteaneCode.read_syndrome(state))


def test_steane_logical_operators():
    lx = SteaneCode.logical_x(0)
    lz = SteaneCode.logical_z(0)
    assert len(lx.lstrip("+-")) == 7
    assert len(lz.lstrip("+-")) == 7


def test_steane_distance():
    assert SteaneCode.distance() == 3


def test_surface_code_parameters():
    assert SurfaceCode3.n == 9
    assert SurfaceCode3.k == 1
    assert len(SurfaceCode3.generators) == 8


def test_surface_code_generators_independent():
    parsed = [_parse_pauli(g) for g in SurfaceCode3.generators]
    mat = [x + z for _, x, z in parsed]
    reduced, _ = _gf2_row_reduce(mat, 18)
    actual_rank = sum(1 for row in reduced if any(row))
    assert actual_rank == 8


def test_surface_code_syndrome_no_error():
    state = SurfaceCode3.zero_state()
    assert SurfaceCode3.read_syndrome(state) == [0] * 8


def test_surface_code_detects_single_error():
    state = SurfaceCode3.zero_state()
    state.x(4)
    assert any(s == 1 for s in SurfaceCode3.read_syndrome(state))


def test_syndrome_extractor_interface():
    state = BitFlip3Code.zero_state()
    ext = BitFlip3Code.syndrome_extractor(state)
    assert ext.extract() == [0, 0]
    state.x(0)
    assert ext.extract() == [1, 0]


def test_custom_code_from_generators():
    code = StabilizerCode(
        n=3,
        k=1,
        generators=["+XXI", "+IXX"],
        name="PhaseFlip",
    )
    state = code.zero_state()
    assert code.read_syndrome(state) == [0, 0]


def test_custom_code_z_error_detected():
    code = StabilizerCode(
        n=3,
        k=1,
        generators=["+XXI", "+IXX"],
        name="PhaseFlip",
    )
    state = code.zero_state()
    state.z(1)
    assert code.read_syndrome(state) != [0, 0]
