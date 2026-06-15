"""
Tests for ancilla management, parity checks, and syndrome extraction.
"""
import pytest

from stabilizer_python import (
    AncillaRegister,
    Circuit,
    StabilizerState,
    SyndromeExtractor,
    mixed_parity_check,
    read_syndrome,
    x_parity_check,
    y_parity_check,
    z_parity_check,
)


def test_add_ancilla_zero_increases_n():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    assert state.n == 3


def test_add_ancilla_zero_tableau_dimensions():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    assert len(state.x_mat) == 6
    assert len(state.z_mat) == 6
    assert all(len(row) == 3 for row in state.x_mat)
    assert all(len(row) == 3 for row in state.z_mat)


def test_add_ancilla_zero_stabilizer_is_z():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    row = state.n + (state.n - 1)
    assert state.x_mat[row][state.n - 1] == 0
    assert state.z_mat[row][state.n - 1] == 1
    assert state.r_phase[row] == 0


def test_add_ancilla_zero_measurement_gives_zero():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    assert state.measure_z(2) == 0


def test_add_ancilla_plus_stabilizer_is_x():
    state = StabilizerState.zero(2)
    state.add_ancilla_plus()
    assert "+IIX" in state.stabilizer_strings()


def test_add_multiple_ancillas():
    state = StabilizerState.zero(3)
    state.add_ancilla_zero()
    state.add_ancilla_zero()
    assert state.n == 5
    assert state.measure_z(3) == 0
    assert state.measure_z(4) == 0


def test_existing_data_stabilizers_unchanged():
    state = StabilizerState.zero(2)
    Circuit(2).h(0).cnot(0, 1).run(state)
    original = state.stabilizer_strings()

    state.add_ancilla_zero()

    for label in original:
        assert label + "I" in state.stabilizer_strings()


def test_remove_ancilla_decreases_n():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    state.remove_ancilla(2)
    assert state.n == 2


def test_remove_ancilla_restores_tableau_dimensions():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    state.remove_ancilla(2)
    assert len(state.x_mat) == 4
    assert len(state.z_mat) == 4
    assert all(len(row) == 2 for row in state.x_mat)


def test_remove_ancilla_out_of_range():
    state = StabilizerState.zero(2)
    with pytest.raises(IndexError):
        state.remove_ancilla(5)


def test_remove_entangled_ancilla_raises():
    state = StabilizerState.zero(2)
    state.add_ancilla_zero()
    state.h(2)
    state.cnot(2, 0)
    with pytest.raises(ValueError):
        state.remove_ancilla(2)


def test_x_parity_plus_plus_state():
    state = StabilizerState.zero(3)
    state.h(0)
    state.h(1)
    assert x_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 0


def test_x_parity_after_z_error_on_plus_state():
    state = StabilizerState.zero(3)
    state.h(0)
    state.h(1)
    state.z(0)
    assert x_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 1


def test_x_parity_ancilla_reset_after_check():
    state = StabilizerState.zero(3)
    state.h(0)
    state.h(1)
    x_parity_check(state, ancilla=2, data_qubits=[0, 1])
    assert state.measure_z(2) == 0


def test_z_parity_all_zero_state():
    state = StabilizerState.zero(3)
    assert z_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 0


def test_z_parity_after_x_error():
    state = StabilizerState.zero(3)
    state.x(0)
    assert z_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 1


def test_z_parity_two_x_errors():
    state = StabilizerState.zero(3)
    state.x(0)
    state.x(1)
    assert z_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 0


def test_z_parity_ancilla_reset():
    state = StabilizerState.zero(3)
    z_parity_check(state, ancilla=2, data_qubits=[0, 1])
    assert state.measure_z(2) == 0


def test_y_parity_y_basis_eigenstate():
    state = StabilizerState.zero(3)
    state.h(0)
    state.s(0)
    state.h(1)
    state.s(1)
    assert y_parity_check(state, ancilla=2, data_qubits=[0, 1]) == 0


def test_mixed_parity_check_zzi():
    state = StabilizerState.zero(4)
    state.x(0)
    assert mixed_parity_check(state, 3, [0, 1, 2], ["Z", "Z", "I"]) == 1


def test_mixed_parity_check_rejects_length_mismatch():
    state = StabilizerState.zero(3)
    with pytest.raises(ValueError):
        mixed_parity_check(state, 2, [0, 1], ["Z"])


def test_ancilla_register_allocates_qubits():
    state = StabilizerState.zero(3)
    register = AncillaRegister(state, names=["s0", "s1"])
    assert state.n == 5
    assert register.n_ancillas() == 2


def test_ancilla_register_named_access():
    state = StabilizerState.zero(3)
    register = AncillaRegister(state, names=["check"])
    assert register.z_parity("check", data_qubits=[0, 1]) in (0, 1)


def test_ancilla_register_reuse():
    state = StabilizerState.zero(3)
    register = AncillaRegister(state, names=["anc"])
    for _ in range(5):
        assert register.z_parity("anc", data_qubits=[0, 1]) in (0, 1)


def test_ancilla_register_unknown_name():
    state = StabilizerState.zero(2)
    register = AncillaRegister(state, names=["a0"])
    with pytest.raises(KeyError):
        register.z_parity("does_not_exist", data_qubits=[0])


def test_ancilla_register_duplicate_names():
    state = StabilizerState.zero(2)
    with pytest.raises(ValueError):
        AncillaRegister(state, names=["a", "a"])


def test_read_syndrome_clean_bitflip3():
    state = StabilizerState.zero(3)
    assert read_syndrome(state, ["ZZI", "IZZ"]) == [0, 0]


def test_read_syndrome_single_x_error_bitflip3():
    state = StabilizerState.zero(3)
    state.x(0)
    assert read_syndrome(state, ["ZZI", "IZZ"]) == [1, 0]


def test_read_syndrome_x_error_qubit1():
    state = StabilizerState.zero(3)
    state.x(1)
    assert read_syndrome(state, ["ZZI", "IZZ"]) == [1, 1]


def test_read_syndrome_x_error_qubit2():
    state = StabilizerState.zero(3)
    state.x(2)
    assert read_syndrome(state, ["ZZI", "IZZ"]) == [0, 1]


def test_read_syndrome_removes_ancilla():
    state = StabilizerState.zero(3)
    n_before = state.n
    read_syndrome(state, ["ZZI", "IZZ"])
    assert state.n == n_before


def test_read_syndrome_invalid_char():
    state = StabilizerState.zero(2)
    with pytest.raises(ValueError):
        read_syndrome(state, ["XA"])


def test_read_syndrome_wrong_length():
    state = StabilizerState.zero(2)
    with pytest.raises(ValueError):
        read_syndrome(state, ["ZZZ"])


def test_syndrome_extractor_init():
    state = StabilizerState.zero(3)
    extractor = SyndromeExtractor(state, ["ZZI", "IZZ"])
    assert extractor.n_checks() == 2
    assert state.n == 4


def test_syndrome_extractor_clean():
    state = StabilizerState.zero(3)
    extractor = SyndromeExtractor(state, ["ZZI", "IZZ"])
    assert extractor.extract() == [0, 0]


def test_syndrome_extractor_with_error():
    state = StabilizerState.zero(3)
    extractor = SyndromeExtractor(state, ["ZZI", "IZZ"])
    state.x(0)
    assert extractor.extract()[0] == 1


def test_syndrome_extractor_repeated_rounds():
    state = StabilizerState.zero(3)
    extractor = SyndromeExtractor(state, ["ZZI", "IZZ"])
    assert extractor.extract() == [0, 0]
    state.x(1)
    assert extractor.extract() == [1, 1]


def test_syndrome_extractor_wrong_operator_length():
    state = StabilizerState.zero(3)
    with pytest.raises(ValueError):
        SyndromeExtractor(state, ["ZZ"])

