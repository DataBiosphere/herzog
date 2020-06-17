import io
import os
import json
import typing
from copy import deepcopy
import __main__
from types import ModuleType
from enum import Enum, auto


class CellType(Enum):
    python = auto()
    markdown = auto()

JUPYTER_SHELL_PFX = "#!"
JUPYTER_MAGIC_PFX = "#%"

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

class ParserObject:
    _translate = {CellType.python: "code", CellType.markdown: "markdown"}

    def __init__(self, definition_line):
        if "Sandbox" in definition_line:
            self.cell_type = CellType.sandbox
        else:
            args, kwargs = _get_args(definition_line.split("(", 1)[1].split(")", 1)[0])
            self.cell_type = CellType[args[0]]
        self._indent = None
        self.lines = list()

    def add_line(self, line):
        if self._indent is None:
            self._indent = line.replace(line.lstrip(), "")
        if line.strip():
            assert line.startswith(self._indent)
        line = line.rstrip()[len(self._indent):]
        if CellType.python == self.cell_type:
            if "pass" == line:
                pass
            elif line.startswith(JUPYTER_SHELL_PFX) or line.startswith(JUPYTER_MAGIC_PFX):
                self.lines.append(line[1:])
            else:
                self.lines.append(line)
        elif CellType.markdown == self.cell_type:
            if "\"\"\"" == line:
                pass
            else:
                self.lines.append(line)

    @property
    def has_ipynb_representation(self):
        return self.cell_type in self._translate

    def to_ipynb_cell(self):
        jupyter_cell = dict(cell_type=self._translate[self.cell_type],
                            metadata=dict(),
                            source=os.linesep.join(self.lines))
        if CellType.python == self.cell_type:
            jupyter_cell.update(dict(execution_count=None, outputs=list()))
        return jupyter_cell

class Parser:
    def __init__(self, handle: io.FileIO):
        self.handle = handle
        self._prev_line = None
        self.objects = [c for c in self._parse_objects()]

    def lines(self):
        for line in self.handle:
            yield line

    def _parse_objects(self):
        for line in self.lines():
            if line.startswith("with herzog.Cell"):
                break
        obj = ParserObject(line)
        for line in self.lines():
            if line.startswith("with herzog.Cell"):
                if obj:
                    yield obj
                obj = ParserObject(line)
            elif not obj and not line.strip():
                pass
            elif obj and not line.strip():
                obj.add_line(line)
            elif obj and obj._indent is None:
                obj.add_line(line)
            elif obj and not line.startswith(obj._indent):
                yield obj
                obj = None
            elif obj and line.startswith(obj._indent):
                obj.add_line(line)
            else:
                continue
        if obj:
            yield obj

def generate(handle: io.FileIO):
    p = Parser(handle)
    cells = [obj.to_ipynb_cell() for obj in p.objects
             if obj.has_ipynb_representation]
    with open(os.path.join(os.path.dirname(__file__), "data", "python_3_boiler.json")) as fh:
        boiler = json.loads(fh.read())
    ipynb = dict(cells=cells, **boiler)
    return ipynb

def _get_args(argstring):
    _getarg = "\n".join((["def getarg(*args, **kwargs):",
                          "    return args, kwargs",
                          "args, kwargs = getarg({})"]))
    global_vars, local_vars = dict(), dict()
    exec(_getarg.format(argstring), global_vars, local_vars)
    return local_vars['args'], local_vars['kwargs']
