"""Draw a maze as coloured blocks for an ANSI terminal."""

import sys
import time

from mazegen.grid import Cell, EAST, SOUTH, Grid

RESET = "\033[0m"
CURSOR_UP = "\033[{lines}A"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

FRAME_DELAY = 0.02
MAX_FRAMES = 80

WALL_PALETTE: tuple[str, ...] = (
    "\033[37m",
    "\033[36m",
    "\033[33m",
    "\033[32m",
    "\033[35m",
    "\033[34m",
)

WALL = "wall"
FLOOR = "floor"
PATH = "path"
ENTRY = "entry"
EXIT = "exit"
PATTERN = "pattern"

CHARS = {
    WALL: "█",
    FLOOR: " ",
    PATH: "█",
    ENTRY: "█",
    EXIT: "█",
    PATTERN: "█",
}

COLOURS = {
    FLOOR: RESET,
    PATH: "\033[97m",
    ENTRY: "\033[95m",
    EXIT: "\033[91m",
    PATTERN: "\033[90m",
}


def render(
    cells: list[list[int]],
    pattern: frozenset[Cell],
    entry: Cell,
    exit_: Cell,
    path: list[Cell],
    palette: int,
) -> str:
    """Return the drawing of a maze, ready to be printed.

    The drawing is a grid of (2 * width + 1) by (2 * height + 1)
    characters, so that every wall and every corridor gets its own
    column and row.

    Args:
        cells: Wall bits of the maze, row by row.
        pattern: Fully closed cells drawing the "42".
        entry: Cell the player enters from.
        exit_: Cell the player leaves from.
        path: Cells of the shortest path, empty when it stays hidden.
        palette: Index of the wall colour to use.

    Returns:
        The lines of the drawing, joined by newlines.
    """
    height = len(cells)
    width = len(cells[0])
    board = [[WALL] * (2 * width + 1) for _ in range(2 * height + 1)]
    for y in range(height):
        for x in range(width):
            walls = cells[y][x]
            board[2 * y + 1][2 * x + 1] = (
                PATTERN if (x, y) in pattern else FLOOR
            )
            if not walls & EAST and x + 1 < width:
                board[2 * y + 1][2 * x + 2] = FLOOR
            if not walls & SOUTH and y + 1 < height:
                board[2 * y + 2][2 * x + 1] = FLOOR
    _draw_path(board, path)
    board[2 * entry[1] + 1][2 * entry[0] + 1] = ENTRY
    board[2 * exit_[1] + 1][2 * exit_[0] + 1] = EXIT
    colours = dict(COLOURS)
    colours[WALL] = WALL_PALETTE[palette % len(WALL_PALETTE)]
    return "\n".join(_draw_row(row, colours) for row in board)


def _draw_path(board: list[list[str]], path: list[Cell]) -> None:
    """Mark the cells of a path and the walls opened between them."""
    for index, cell in enumerate(path):
        board[2 * cell[1] + 1][2 * cell[0] + 1] = PATH
        if index:
            previous = path[index - 1]
            board[cell[1] + previous[1] + 1][cell[0] + previous[0] + 1] = (
                PATH
            )


def _draw_row(row: list[str], colours: dict[str, str]) -> str:
    """Return one row of the drawing, with as few escape codes as can be."""
    parts: list[str] = []
    current = ""
    for kind in row:
        colour = colours[kind]
        if colour != current:
            parts.append(colour)
            current = colour
        parts.append(CHARS[kind])
    parts.append(RESET)
    return "".join(parts)


def animate_build(
    width: int,
    height: int,
    pattern: frozenset[Cell],
    steps: list[tuple[Cell, Cell]],
    endpoints: tuple[Cell, Cell],
    palette: int,
) -> None:
    """Replay a generation, one opened wall at a time.

    The walls are opened again on a fresh grid holding only the "42"
    pattern, and the board is redrawn in place every few steps, so the
    depth-first walk that carved the maze can be watched. The number of
    frames is capped, so a large board is not slower to watch than a
    small one.

    Args:
        width: Number of cells along the horizontal axis.
        height: Number of cells along the vertical axis.
        pattern: Fully closed cells drawing the "42".
        steps: Walls opened by the generation, in order.
        endpoints: Entry and exit of the maze.
        palette: Index of the wall colour to use.
    """
    grid = Grid(width, height)
    for cell in sorted(pattern):
        grid.block(cell)
    entry, exit_ = endpoints
    stride = max(1, len(steps) // MAX_FRAMES)
    try:
        sys.stdout.write(HIDE_CURSOR)
        print(render(grid.snapshot(), pattern, entry, exit_, [], palette))
        for index, (source, target) in enumerate(steps, start=1):
            grid.open_wall(source, target)
            if index % stride and index != len(steps):
                continue
            _replace(
                height,
                render(
                    grid.snapshot(), pattern, entry, exit_, [], palette
                ),
            )
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


def animate_path(
    cells: list[list[int]],
    pattern: frozenset[Cell],
    endpoints: tuple[Cell, Cell],
    path: list[Cell],
    palette: int,
) -> None:
    """Draw a solution one step at a time over an already drawn maze.

    Args:
        cells: Wall bits of the maze, row by row.
        pattern: Fully closed cells drawing the "42".
        endpoints: Entry and exit of the maze.
        path: Cells of the shortest path.
        palette: Index of the wall colour to use.
    """
    entry, exit_ = endpoints
    height = len(cells)
    stride = max(1, len(path) // MAX_FRAMES)
    try:
        sys.stdout.write(HIDE_CURSOR)
        for index in range(1, len(path) + 1):
            if index % stride and index != len(path):
                continue
            _replace(
                height,
                render(
                    cells, pattern, entry, exit_, path[:index], palette
                ),
            )
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


def _replace(height: int, drawing: str) -> None:
    """Draw a frame over the one already printed, then wait a moment."""
    sys.stdout.write(CURSOR_UP.format(lines=2 * height + 1))
    sys.stdout.write(f"{drawing}\n")
    sys.stdout.flush()
    time.sleep(FRAME_DELAY)
