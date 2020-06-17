import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import herzog


with herzog.Cell("markdown"):
    """
    # This is a header
    doom and gloom

    ## frank is a ganster
    evidence
    """

# Anything placed outside of a Cell context manager will not
# be included in a cell. This is a good place for dev notes that should
# not be included in published notebooks.

with herzog.Cell("python"):
    import os
    print("blaksdjf")
    foo = 3

    doom = "frank"
    comp = dict(c=dict(a="b"))

# Save and restore context. As long as you don't do anything crazy,
# the program will return to it's previous state after a Sandbox context.
# This is a good place to put test logic that transforms variables.
with herzog.Sandbox():
    assert foo == 3
    doom = "gloom"
    comp["c"]["a"] = "You should not see this message."

with herzog.Cell("python"):
    foo += 21
    print(os.path)
    print(doom)
    print(comp)
