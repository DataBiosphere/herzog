import os
import ast
from enum import Enum, auto
from typing import Generator, Iterable, List, Optional, TextIO, Dict, Any


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
                if line in ('"""', "pass"):
                    pass
                else:
                    self.lines.append(line)

    @property
    def has_ipynb_representation(self) -> bool:
        return self.cell_type in self._translate

    def to_ipynb_cell(self) -> Dict[str, Any]:
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

def parse_cell_type(s: str) -> str:
    # TODO: Make this account for other valid cases like comments or multi-line, for example:
    # with herzog.Cell(
    #     'python'
    # )
    #
    # or
    #
    # with herzog.Cell('python'):  # noqa
    #
    return s.strip()[len("with herzog.Cell("):-len("):")].strip().strip('"').strip("'").strip()

def parse_cells(raw_lines: TextIO) -> Generator[HerzogCell, None, None]:
    lines = [line for line in raw_lines]
    for node in ast.walk(ast.parse(''.join(lines))):
        if isinstance(node, ast.With):
            indent = node.body[0].col_offset
            if node.items and isinstance(node.items[0].context_expr, ast.Call) and node.items[0].context_expr.args:
                ast_call = node.items[0].context_expr
                if "herzog" == ast_call.func.value.id and "Cell" == ast_call.func.attr:  # type: ignore
                    cell_type = CellType[ast_call.args[0].value]  # type: ignore
                    cell_lines = [line[indent:].rstrip()
                                  for line in lines[node.body[0].lineno - 1: node.body[-1].end_lineno]]
                    yield HerzogCell(cell_type, cell_lines)
