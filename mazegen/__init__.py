"""Generate reusable mazes with a "42" pattern and a shortest path.

The package exposes a single generation class, ``MazeGenerator``. It
depends on nothing but the Python standard library, reads and writes no
file and prints nothing, so it can be dropped into any other project.

Basic usage:

    from mazegen import MazeGenerator

    generator = MazeGenerator(
        width=20,
        height=15,
        entry=(0, 0),
        exit_=(19, 14),
        perfect=False,
        seed=42,
    )
    generator.generate()

Custom parameters:

    ``width`` and ``height`` are the size of the board in cells, and
    must both be at least 2. ``entry`` and ``exit_`` are ``(x, y)``
    cells, where ``x`` is the column and ``y`` the row counted from the
    top; they must lie inside the board and differ from each other.
    ``perfect`` selects the generation mode: ``True`` builds a perfect
    maze, holding exactly one path between the entry and the exit,
    while ``False`` builds a braided board that stays fully connected,
    keeps its four corners and its centre open and offers at least two
    independent routes. ``seed`` makes a generation reproducible: the
    same seed and the same parameters always rebuild the same maze. It
    may be omitted, in which case a random seed is drawn and exposed as
    ``generator.seed``.

Accessing the structure:

    ``generator.cells`` is a list of rows of packed wall bits, one
    integer per cell, where bit 0 is the north wall, bit 1 the east
    wall, bit 2 the south wall and bit 3 the west wall. A bit set to 1
    means the wall is closed. ``generator.to_hex_lines()`` returns the
    same board as one lowercase hexadecimal string per row, and
    ``generator.pattern_cells`` returns the fully closed cells drawing
    the "42", which is empty when the board was too small to host it.

Accessing a solution:

    ``generator.solution()`` returns the shortest path from the entry
    to the exit as a list of ``(x, y)`` cells, and
    ``generator.solution_directions()`` returns the same path as a
    string of the letters N, E, S and W.

Replaying a generation:

    ``generator.build_steps()`` returns the walls the generation
    opened, in order, as pairs of neighbouring cells. Opening them one
    by one on a fresh grid that only holds ``generator.pattern_cells``
    rebuilds the very same maze, which is what an animation of the
    generation needs. The package draws nothing itself: it only hands
    over the steps.

Every failure raises a subclass of ``MazeError``:
``InvalidParametersError`` for unusable constructor arguments, and
``MazeGenerationError`` when no board matching the requested rules
could be built.
"""

from mazegen.errors import (
    InvalidParametersError,
    MazeError,
    MazeGenerationError,
)
from mazegen.generator import MazeGenerator

__version__ = "1.0.0"

__all__ = [
    "InvalidParametersError",
    "MazeError",
    "MazeGenerationError",
    "MazeGenerator",
    "__version__",
]
