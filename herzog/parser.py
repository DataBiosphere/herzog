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
    cell_type: CellType
    has_ipynb_representation: bool

    def to_ipynb_cell(self) -> Dict[str, Any]:
        raise NotImplementedError()

class PythonCell(HerzogCell):
    cell_type = CellType.python
    has_ipynb_representation = True

    def __init__(self, indent: int, lines: Iterable[str]):
        self.lines = list()
        for line in lines:
            line = line[indent:].rstrip() + os.linesep
            if "pass" == line:
                pass
            elif line.startswith(JUPYTER_SHELL_PFX) or line.startswith(JUPYTER_MAGIC_PFX):
                self.lines.append(line[1:])
            else:
                self.lines.append(line)

    def to_ipynb_cell(self) -> Dict[str, Any]:
        return dict(cell_type="code",
                    metadata=dict(),
                    source=self.lines,
                    execution_count=None,
                    outputs=list())

class MarkdownCell(HerzogCell):
    cell_type = CellType.markdown
    has_ipynb_representation = True

    def __init__(self, indent: int, text: str):
        lines = text.split(os.linesep)
        while lines:
            if not lines[0].strip():
                lines.pop(0)
            else:
                break
        while lines:
            if not lines[-1].strip():
                lines.pop()
            else:
                break
        self.lines = [line[indent:] + os.linesep for line in lines]

    def to_ipynb_cell(self) -> Dict[str, Any]:
        return dict(cell_type="markdown",
                    metadata=dict(),
                    source=self.lines)

def parse_cells(raw_lines: TextIO) -> Generator[HerzogCell, None, None]:
    lines = [line for line in raw_lines]
    for node in ast.walk(ast.parse(''.join(lines))):
        if isinstance(node, ast.With):
            indent = node.body[0].col_offset
            if node.items and isinstance(node.items[0].context_expr, ast.Call) and node.items[0].context_expr.args:
                ast_call = node.items[0].context_expr
                if "herzog" == ast_call.func.value.id and "Cell" == ast_call.func.attr:  # type: ignore
                    cell_type = CellType[ast_call.args[0].value]  # type: ignore
                    if CellType.python == cell_type:
                        yield PythonCell(indent, lines[node.body[0].lineno - 1: node.body[-1].end_lineno])
                    elif CellType.markdown == cell_type:
                        yield MarkdownCell(indent, node.body[0].value.value)  # type: ignore
