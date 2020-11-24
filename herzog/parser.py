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

    def __init__(self, cell_type: CellType, lines: Iterable[str]):
        self.cell_type = cell_type
        self.lines: List[str] = list()
        for line in lines:
            if CellType.python == self.cell_type:
                if "pass" == line:
                    pass
                elif line.startswith(JUPYTER_SHELL_PFX) or line.startswith(JUPYTER_MAGIC_PFX):
                    self.lines.append(line[1:])
                else:
                    self.lines.append(line)
            elif CellType.markdown == self.cell_type:
                if '"""' == line:
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

def _parse_cell(lines: _RewindableIterator) -> Generator[str, None, None]:
    indent: Optional[str] = None
    for line in lines:
        if indent is None:
            indent = line.replace(line.lstrip(), "")
        if not line.strip():
            yield ""  # allow vertical whitespace
        elif line.startswith(indent):
            yield line.rstrip()[len(indent):]
        else:
            break

def _validate_cell(cell_lines: List[str], line_number: Optional[int]=None):
    line_number_str = str(line_number) if line_number is not None else "?"
    if not cell_lines:
        raise SyntaxError(f"line {line_number_str}: Expected Herzog cell content")
    else:
        try:
            compile(os.linesep.join(cell_lines), "", "exec")
        except SyntaxError:
            raise SyntaxError(f"line {line_number_str}")

def parse_cells(raw_lines: TextIO) -> Generator[HerzogCell, None, None]:
    rlines = _RewindableIterator(raw_lines)
    for line in rlines:
        if "with herzog.Cell" in line:
            cell_type_string = line.strip()[len("with herzog.Cell"):].strip('"():')
            cell_type = CellType[cell_type_string]
            line_number = rlines.item_number
            cell_lines = [line for line in _parse_cell(rlines)]
            while cell_lines and not cell_lines[-1]:  # Strip whitespace off end of cell
                cell_lines.pop()
            _validate_cell(cell_lines, line_number)
            rlines.rewind()
            yield HerzogCell(cell_type, cell_lines)
