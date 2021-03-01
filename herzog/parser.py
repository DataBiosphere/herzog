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
