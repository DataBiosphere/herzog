#!/usr/bin/env python
import os
import sys
import json
import unittest
import subprocess

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import herzog


class TestHerzog(unittest.TestCase):
    def test_evaluate(self):
        p = subprocess.run([f"{sys.executable}", "tests/fixtures/example.py"])
        p.check_returncode()

    def test_parser(self):
        with open("tests/fixtures/fibonacci.py") as fh:
            p = herzog.Parser(fh)
            cells = [obj.to_ipynb_cell() for obj in p.objects
                     if obj.has_ipynb_representation]
        with open("tests/fixtures/fibonacci.ipynb") as fh:
            expected = json.loads(fh.read())

        for cell, expected_cell in zip(cells, expected['cells']):
            self.assertEqual(cell, expected_cell)

    def test_generate(self):
        with open("tests/fixtures/example.py") as fh:
            herzog.generate(fh)


if __name__ == '__main__':
    unittest.main()
