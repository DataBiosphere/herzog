import os
import sys
import json
from copy import deepcopy
import __main__
import textwrap
from types import ModuleType
from typing import TextIO, Dict, Any, Generator, List
from herzog.parser import parse_cells, CellType, JUPYTER_SHELL_PFX, JUPYTER_MAGIC_PFX

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
        return json.loads(ipynb.read())['cells']
    except (json.JSONDecodeError, KeyError):
        print(f"Check that '{ipynb}' is a valid ipynb file.", file=sys.stderr)
        raise

def translate_to_ipynb(herzog_handle: TextIO) -> Dict[str, Any]:
    cells = [obj.to_ipynb_cell() for obj in parse_cells(herzog_handle)
             if obj.has_ipynb_representation]
    with open(os.path.join(os.path.dirname(__file__), "data", "python_3_boiler.json")) as fh:
        boiler = json.loads(fh.read())
    return dict(cells=cells, **boiler)

def translate_to_herzog(ipynb_handle: TextIO, indent: int = 4) -> Generator[str, None, None]:
    cells = load_ipynb_cells(ipynb_handle)
    prefix = " " * indent
    yield "import herzog\n\n"

    for cell in cells:
        if isinstance(cell.get('source', None), list):
            cell['source'] = "".join(cell['source'])

        if cell['cell_type'] == "markdown":
            s = '\nwith herzog.Cell("markdown"):\n    """\n'
            s += textwrap.indent(cell['source'], prefix=prefix).rstrip()
            s += '\n    """\n'
            for line in s.split("\n"):
                yield line + "\n"
        elif cell['cell_type'] == "code":
            s = "\nwith herzog.Cell('python'):\n"
            s += textwrap.indent(cell['source'], prefix=prefix).rstrip()
            for line in s.split("\n"):
                if line.startswith("%"):
                    yield line.replace("%", JUPYTER_MAGIC_PFX, 1) + "\n"
                elif line.startswith("!"):
                    yield line.replace("!", JUPYTER_SHELL_PFX, 1) + "\n"
                else:
                    yield line + "\n"
        else:
            print(f"cell_type not implemented yet: {cell['cell_type']}", file=sys.stderr)
            # warn the user and add, but comment out
            yield "\n"
            yield "## .ipynb -> Herzog translation failed:\n"
            yield f"## Cell type '{cell['source']}' not supported by Herzog. " \
                  f"Supported cell types are {CellType._member_names_}\n"
            yield f"# with herzog.Cell('{cell['cell_type']}'):\n"
            s = textwrap.indent(cell['source'], prefix=prefix).rstrip() + "\n"
            for line in s.split("\n"):
                yield f"# {line}\n"
