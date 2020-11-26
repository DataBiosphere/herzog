import io
import os
from enum import Enum, auto
from typing import Generator, TextIO


class CellType(Enum):
    python = auto()
    markdown = auto()

JUPYTER_SHELL_PFX = "#!"
JUPYTER_MAGIC_PFX = "#%"

class HerzogCell:
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
        while self.lines and not self.lines[-1]:
            # Strip whitespace off end of cell
            self.lines.pop()
        jupyter_cell = dict(cell_type=self._translate[self.cell_type],
                            metadata=dict(),
                            source=os.linesep.join(self.lines))
        if CellType.python == self.cell_type:
            jupyter_cell.update(dict(execution_count=None, outputs=list()))
        return jupyter_cell

def parse_cells(handle: TextIO) -> Generator[HerzogCell, None, None]:
    for line in handle:
        if line.startswith("with herzog.Cell"):
            break
    obj = HerzogCell(line)
    for line in handle:
        if line.startswith("with herzog.Cell"):
            if obj:
                yield obj
            obj = HerzogCell(line)
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

def _get_args(argstring):
    _getarg = "\n".join((["def getarg(*args, **kwargs):",
                          "    return args, kwargs",
                          "args, kwargs = getarg({})"]))
    global_vars, local_vars = dict(), dict()
    exec(_getarg.format(argstring), global_vars, local_vars)
    return local_vars['args'], local_vars['kwargs']
