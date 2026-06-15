from stabilizer_python.codes import BitFlip3Code
from stabilizer_python.tableau import StabilizerState
from stabilizer_python.tracing import TracedCircuit


def main() -> None:
    st = StabilizerState.zero(5)
    BitFlip3Code.encoder_circuit().run(st)
    print("Encoded |0_L> on qubits 0-2 with ancillas 3-4 in |0>:")
    print(st.inspect())
    print()

    st.x(1)
    print("After injecting X on data qubit 1:")
    print(st.inspect(views=["stabilizers"]))
    print()

    tc = TracedCircuit(BitFlip3Code.syndrome_circuit(), trace=True)
    outcomes = tc.run(st)
    print("Syndrome outcomes (s01, s12):", tuple(outcomes))
    print()
    tc.print_trace()


if __name__ == "__main__":
    main()
