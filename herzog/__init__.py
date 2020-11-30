import os
import json
from copy import deepcopy
import __main__
from types import ModuleType
from typing import TextIO

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

def generate(handle: TextIO):
    cells = [obj.to_ipynb_cell() for obj in parse_cells(handle)
             if obj.has_ipynb_representation]
    with open(os.path.join(os.path.dirname(__file__), "data", "python_3_boiler.json")) as fh:
        boiler = json.loads(fh.read())
    ipynb = dict(cells=cells, **boiler)
    return ipynb
