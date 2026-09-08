"""Place the fully closed cells that draw a "42" inside the maze."""

from collections import deque

from mazegen.grid import Cell

PATTERN_42: tuple[str, ...] = (
    "X...XXX",
    "X.....X",
    "X.....X",
    "XXX.XXX",
    "..X.X..",
    "..X.X..",
    "..X.XXX",
)

MARK = "X"

MIN_CORRIDOR_NEIGHBOURS = 2


def pattern_size() -> Cell:
    """Return the width and height of the "42" bitmap, in cells."""
    return len(PATTERN_42[0]), len(PATTERN_42)


def place_pattern(
    width: int,
    height: int,
    forbidden: frozenset[Cell],
) -> frozenset[Cell]:
    """Return the cells drawing a "42", as close to the centre as possible.

    The bitmap is first tried at the centred position, then at every
    other position ordered by growing distance from that centre. A
    position is kept only when it covers no forbidden cell, leaves the
    corridor graph connected and leaves every corridor cell with at
    least two corridor neighbours, so that dead-ends stay removable.

    Args:
        width: Number of cells along the horizontal axis.
        height: Number of cells along the vertical axis.
        forbidden: Cells the pattern is never allowed to cover.

    Returns:
        The cells to seal, or an empty set when the grid is too small
        or too constrained to host the pattern.
    """
    pattern_width, pattern_height = pattern_size()
    if width < pattern_width or height < pattern_height:
        return frozenset()
    centre_x = (width - pattern_width) // 2
    centre_y = (height - pattern_height) // 2
    origins = [
        (x, y)
        for y in range(height - pattern_height + 1)
        for x in range(width - pattern_width + 1)
    ]
    origins.sort(
        key=lambda origin: (
            abs(origin[0] - centre_x) + abs(origin[1] - centre_y),
            abs(origin[1] - centre_y),
            abs(origin[0] - centre_x),
            origin[1],
            origin[0],
        )
    )
    for origin in origins:
        cells = _cells_at(origin)
        if cells & forbidden:
            continue
        if _is_placeable(width, height, cells):
            return frozenset(cells)
    return frozenset()


def _cells_at(origin: Cell) -> set[Cell]:
    """Return the cells covered by the bitmap stamped at an origin."""
    return {
        (origin[0] + x, origin[1] + y)
        for y, row in enumerate(PATTERN_42)
        for x, mark in enumerate(row)
        if mark == MARK
    }


def _is_placeable(width: int, height: int, cells: set[Cell]) -> bool:
    """Tell whether sealing a set of cells keeps the maze buildable."""
    corridors = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in cells
    ]
    if not corridors:
        return False
    for cell in corridors:
        if len(_free_neighbours(width, height, cell, cells)) < (
            MIN_CORRIDOR_NEIGHBOURS
        ):
            return False
    return _is_connected(width, height, corridors, cells)


def _free_neighbours(
    width: int,
    height: int,
    cell: Cell,
    cells: set[Cell],
) -> list[Cell]:
    """Return the in-bounds neighbours left outside the sealed set."""
    x, y = cell
    candidates = ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y))
    return [
        (nx, ny)
        for nx, ny in candidates
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in cells
    ]


def _is_connected(
    width: int,
    height: int,
    corridors: list[Cell],
    cells: set[Cell],
) -> bool:
    """Tell whether every corridor cell remains mutually reachable."""
    start = corridors[0]
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for other in _free_neighbours(width, height, cell, cells):
            if other not in seen:
                seen.add(other)
                queue.append(other)
    return len(seen) == len(corridors)
