#!/usr/bin/env python
import io
import os
import sys
import json
import unittest
import subprocess

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import herzog


class TestHerzog(unittest.TestCase):
    def test_parser(self):
        with open("tests/fixtures/example.py", "r") as fh:
            cells = self._gen_cells_from_content(fh.read())

        with open("tests/fixtures/example.ipynb", "r") as fh:
            expected_cells = json.loads(fh.read())['cells']

        self.assertEqual(len(expected_cells), len(cells))
        for expected_cell, cell in zip(expected_cells, cells):
            self.assertEqual(expected_cell, cell)

    def _gen_cells_from_content(self, content: str):
        p = herzog.Parser(io.StringIO(content))  # type: ignore
        return [obj.to_ipynb_cell() for obj in p.objects
                if obj.has_ipynb_representation]

    def test_generate(self):
        with open("tests/fixtures/example.py") as fh:
            herzog.generate(fh)


if __name__ == '__main__':
    unittest.main()
