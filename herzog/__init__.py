import os
import sys
import json
from copy import deepcopy
import __main__
import textwrap
from types import ModuleType
from typing import TextIO, Dict, Any, Optional, List
from herzog.parser import parse_cells, CellType


class Cell:
    def __init__(self, cell_type):
        self.cell_type = CellType[cell_type]

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return None

class Sandbox:
    def __init__(self):
        self._state = None
        self._state_modules = None

    def __enter__(self):
        self._state = deepcopy({k: v for k, v in __main__.__dict__.items()
                                if not isinstance(v, ModuleType)})
        self._state_modules = {k: v for k, v in __main__.__dict__.items()
                               if isinstance(v, ModuleType)}
        return self

    def __exit__(self, *args, **kwargs):
        if self._state:
            __main__.__dict__.update(self._state)
            for key in __main__.__dict__.copy():
                if key not in self._state:
                    del __main__.__dict__[key]
            __main__.__dict__.update(self._state_modules)

def load_ipynb_cells(ipynb: TextIO) -> List[Dict[Any, Any]]:
    try:
        cells = json.loads(ipynb.read()).get('cells', None)
    except Exception:
        print(f'Check that "{ipynb}" is a valid ipynb file.', file=sys.stderr)
        raise

    if not cells:
        print(f'Python notebook: "{ipynb}" has no cells.\nNothing to be done.  Exiting... ')
        exit()
    return cells

def generate(handle: TextIO, input_type: Optional[str] = 'herzog') -> str:
    if input_type == 'herzog':
        return translate_to_ipynb(handle)
    elif input_type == 'ipynb':
        return translate_to_herzog(handle)
    else:
        raise NotImplementedError(f'source_type: "{input_type}" not supported.')

def translate_to_ipynb(herzog_handle: TextIO, indent: int = 2) -> str:
    cells = [obj.to_ipynb_cell() for obj in parse_cells(herzog_handle)
             if obj.has_ipynb_representation]
    with open(os.path.join(os.path.dirname(__file__), "data", "python_3_boiler.json")) as fh:
        boiler = json.loads(fh.read())
    ipynb = json.dumps(dict(cells=cells, **boiler), indent=indent)
    return ipynb

def translate_to_herzog(ipynb_handle: TextIO, indent: int = 4) -> str:
    cells = load_ipynb_cells(ipynb_handle)
    python_prefix = ' ' * indent
    markdown_prefix = python_prefix + '# '
    script = 'import herzog\n\n'

    for cell in cells:
        if isinstance(cell.get('source', None), list):
            cell['source'] = ''.join(cell['source'])

        if cell['cell_type'] == 'markdown':
            script += "\nwith herzog.Cell('markdown'):\n"
            script += textwrap.indent(cell['source'], prefix=markdown_prefix, predicate=lambda x: True).rstrip()
            script += "\n    pass\n"
        elif cell['cell_type'] == 'code':
            script += "\nwith herzog.Cell('python'):\n"
            script += textwrap.indent(cell['source'], prefix=python_prefix).rstrip()
        else:
            raise NotImplementedError(f"cell_type not implemented yet: {cell['cell_type']}")
    return script
