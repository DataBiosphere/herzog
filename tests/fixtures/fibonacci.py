import herzog

with herzog.Cell("markdown"):
    """
    # Fibonacci
    Recursively generate terms from the Fibonacci sequence.
    """

with herzog.Cell("python"):
    def fibonacci(term: int) -> int:
        """
        0-indexed fibonacci
        """
        assert 0 <= term
        if 1 < term:
            return fibonacci(term - 1) + fibonacci(term - 2)
        else:
            return term

# Code outside herzog context does not appear in generated notebooks.
try:
    fibonacci(-1)
except AssertionError:
    # expected
    pass
expected_fibonacci = (0, 1, 1, 2, 3, 5, 8, 13, 21)
for i in range(1, len(expected_fibonacci)):
    assert expected_fibonacci[i] == fibonacci(i)

golden_ratio = (1 + 5 ** 0.5) / 2
assert 1e-10 > abs(golden_ratio - fibonacci(26) / fibonacci(25))
