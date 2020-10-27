# herzog

Write your Python [Jupyter](https://jupyter.org/) notebooks in herzog!

herzog scripts are pure Python. This means version control, pull requests, CI/CD, and more.

Great! How does it work?

## Usage

Use context managers to define Jupyter cells:
```
with herzog.Cell("python"):
    print("Hello herzog")
```

Want to tell your users what to do? Make a markdown cell:
```
with herzog.Cell("markdown"):
    """
    # How cool is this notebook?
    So cool!
    """
```

Use the herzog CLI to generate a notebook from your Python script:
```
herzog path/to/my/cool_script.py > path/to/my/cool_notebook.ipynb
```

### Example

An example herzog script is shown below, along with the generated notebook. Both the
[herzog source](https://github.com/xbrianh/herzog/blob/master/tests/fixtures/fibonacci.py)
and
[generated notebook](https://github.com/xbrianh/herzog/blob/master/tests/fixtures/fibonacci.ipynb)
can be found in the herzog repository.

Note that everything outside herzog context managers is not included in the notebook. That's where you put tests,
developer notes, salacious accusations, or anything else.
```
import herzog

with herzog.Cell("markdown"):
    """
    # Fibonacci:
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
```

![Rendered Fibonacci notebook](https://github.com/xbrianh/herzog/blob/master/tests/fixtures/fibonacci_rendered.png)

## Installation

```
pip install herzog
```

## Links

Project home page [GitHub](https://github.com/xbrianh/herzog)  
Package distribution [PyPI](https://pypi.org/project/herzog/)

### Bugs

Please report bugs, issues, feature requests, etc. on [GitHub](https://github.com/xbrianh/herzog).

![](https://travis-ci.com/xbrianh/herzog.svg?branch=master) ![](https://badge.fury.io/py/herzog.svg)
