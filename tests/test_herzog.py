#!/usr/bin/env python
import io
import os
import sys
import json
import unittest
import subprocess

from typing import List
from uuid import uuid4

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import herzog


class TestHerzog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    def setUp(self) -> None:
        self.cleanup: List[str] = []

    def tearDown(self) -> None:
        for cruft in self.cleanup:
            if os.path.exists(cruft):
                os.remove(cruft)

    def test_parser(self):
        with open("tests/fixtures/example.py", "r") as fh:
            cells = self._gen_cells_from_content(fh.read())

        with open("tests/fixtures/example.ipynb", "r") as fh:
            expected_cells = json.loads(fh.read())['cells']

        self.assertEqual(len(expected_cells), len(cells))
        for expected_cell, cell in zip(expected_cells, cells):

            # convert all "source" to "string"; equally valid as a list or a string, example:
            #     '# This is a header\ndoom and gloom\n\n## frank is a gangster\nevidence'
            #     ['# This is a header\n', 'doom and gloom\n', '\n', '## frank is a gangster\n', 'evidence']
            if isinstance(expected_cell.get('source', None), list):
                expected_cell['source'] = ''.join(expected_cell['source'])

            self.assertEqual(expected_cell, cell, f'\n{expected_cell}\n{cell}')

    def test_cli_two_way_conversion(self):
        """
        Make sure that if we convert back and forth multiple times, it always gives the same file.

        Note:
            Content outside of the "with herzog.Cell()" context manager is always lost as it does
            not become a part of the python notebook.
        """
        ipynb_0 = 'tests/fixtures/example.ipynb'

        py_generated_1 = f'delete-{uuid4()}.py'
        ipynb_generated_2 = f'delete-{uuid4()}.ipynb'
        py_generated_3 = f'delete-{uuid4()}.py'
        self.cleanup += [py_generated_1, ipynb_generated_2, py_generated_3]

        with open(ipynb_0) as f:
            ipynb_0_content = json.loads(f.read())
            for cell in ipynb_0_content.get('cells', []):
                # convert all "source" to "string"; equally valid as a list or a string, example:
                #     '# This is a header\ndoom and gloom\n\n## frank is a gangster\nevidence'
                #     ['# This is a header\n', 'doom and gloom\n', '\n', '## frank is a gangster\n', 'evidence']
                if isinstance(cell.get('source', None), list):
                    cell['source'] = ''.join(cell['source'])

        cmd = ['scripts/herzog', 'convert', '-i', f'{ipynb_0}', '-o', f'{py_generated_1}']
        subprocess.run(cmd, check=True)
        with open(py_generated_1) as f:
            py_generated_1_content = f.read()

        cmd = ['scripts/herzog', 'convert', '-i', f'{py_generated_1}', '-o', f'{ipynb_generated_2}']
        subprocess.run(cmd, check=True)
        with open(ipynb_generated_2) as f:
            ipynb_generated_2_content = json.loads(f.read())

        for ipynb in [ipynb_generated_2_content, ipynb_0_content]:
            if 'pycharm' in ipynb.get('metadata', {}):
                # only appears if generated through pycharm
                del ipynb['metadata']['pycharm']

        assert ipynb_generated_2_content == ipynb_0_content, f'\n\n{ipynb_generated_2_content}\n{ipynb_0_content}'

        cmd = ['scripts/herzog', 'convert', '-i', f'{ipynb_generated_2}', '-o', f'{py_generated_3}']
        subprocess.run(cmd, check=True)
        with open(py_generated_3) as f:
            py_generated_3_content = f.read()

        assert py_generated_1_content == py_generated_3_content

    def test_parser_errors(self):
        tests = {
            'Empty Herzog context manager': r'with herzog.Cell("python"):',
            'Incorrect syntax': os.linesep.join((r'with herzog.Cell("python"):',
                                                 r'    int("frank"')),
            'Double cell definitions': os.linesep.join((r'with herzog.Cell("python"):',
                                                        r'with herzog.Cell("python"):'))
        }
        for test_name, cell_content in tests.items():
            with self.subTest(test_name):
                with self.assertRaises(SyntaxError):
                    self._gen_cells_from_content(cell_content)

    def _gen_cells_from_content(self, content: str):
        return [cell.to_ipynb_cell() for cell in herzog.parse_cells(io.StringIO(content))
                if cell.has_ipynb_representation]

    def test_generate(self):
        with open("tests/fixtures/example.py") as fh:
            herzog.generate(fh)


if __name__ == '__main__':
    unittest.main()
