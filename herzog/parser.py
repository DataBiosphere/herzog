import io
import os
from enum import Enum, auto
from typing import Generator, Iterable, List, Optional, TextIO


class CellType(Enum):
    python = auto()
    markdown = auto()
    sandbox = auto()

JUPYTER_SHELL_PFX = "#!"
JUPYTER_MAGIC_PFX = "#%"

class HerzogCell:
    _translate = {CellType.python: "code", CellType.markdown: "markdown"}

    def __init__(self, definition_line):
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

class _RewindableIterator:
    def __init__(self, iterable: Iterable):
        self._iterable = iterable
        self._prev: Optional[str] = None
        self._rewind = False
        self.item_number = 0

    def __next__(self):
        if self._rewind and self._prev is not None:
            item = self._prev
            self._rewind = False
        else:
            item = next(self._iterable)
            self._prev = item
            self.item_number += 1
        return item

    def __iter__(self):
        try:
            while True:
                yield next(self)
        except StopIteration:
            pass

    def rewind(self):
        self._rewind = True

def _validate_cell(cell_lines: List[str], line_number: Optional[int]=None):
    line_number_str = str(line_number) if line_number is not None else "?"
    if not cell_lines:
        raise SyntaxError(f"line {line_number_str}: Expected Herzog cell content")
    else:
        try:
            compile(os.linesep.join(cell_lines), "", "exec")
        except SyntaxError:
            raise SyntaxError(f"line {line_number_str}")

def parse_cells(handle: TextIO) -> Generator[HerzogCell, None, None]:
    for line in handle:
        if line.startswith("with herzog.Cell"):
            break
    obj = HerzogCell(line)
    for line in handle:
        if line.startswith("with herzog.Cell"):
            if obj:
                _validate_cell(obj.lines)
                yield obj
            obj = HerzogCell(line)
        elif not obj and not line.strip():
            pass
        elif obj and not line.strip():
            obj.add_line(line)
        elif obj and obj._indent is None:
            obj.add_line(line)
        elif obj and not line.startswith(obj._indent):
            _validate_cell(obj.lines)
            yield obj
            obj = None
        elif obj and line.startswith(obj._indent):
            obj.add_line(line)
        else:
            continue
    if obj:
        _validate_cell(obj.lines)
        yield obj

def _get_args(argstring):
    _getarg = "\n".join((["def getarg(*args, **kwargs):",
                          "    return args, kwargs",
                          "args, kwargs = getarg({})"]))
    global_vars, local_vars = dict(), dict()
    exec(_getarg.format(argstring), global_vars, local_vars)
    return local_vars['args'], local_vars['kwargs']
