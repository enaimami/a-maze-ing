"""Check that a generated maze honours every rule of the subject."""

from collections import deque

from mazegen.grid import (
    ALL_WALLS,
    OPPOSITE,
    ORDER,
    STEPS,
    Cell,
    Grid,
)

BLOCK_SIDE = 3
MAX_DEAD_ENDS = 2
MIN_LOOPS = 2


def validate(
    grid: Grid,
    entry: Cell,
    exit_: Cell,
    perfect: bool,
) -> list[str]:
    """Return every rule the maze breaks, as readable messages.

    Args:
        grid: Maze to inspect.
        entry: Cell the player enters from.
        exit_: Cell the player leaves from.
        perfect: Whether a single path between entry and exit is wanted.

    Returns:
        An empty list when the maze is valid, the list of broken rules
        otherwise.
    """
    problems: list[str] = []
    problems.extend(_check_endpoints(grid, entry, exit_))
    problems.extend(_check_sealed_cells(grid))
    problems.extend(_check_borders(grid))
    problems.extend(_check_wall_coherence(grid))
    if has_open_area(grid):
        problems.append("the maze contains a fully open 3x3 area")
    if problems:
        return problems
    corridors = grid.corridors()
    if len(_reachable(grid, entry)) != len(corridors):
        return ["some corridor cells cannot be reached"]
    if perfect:
        return _check_perfect(grid, corridors)
    return _check_playable(grid, corridors)


def loop_count(grid: Grid, corridors: list[Cell]) -> int:
    """Return how many independent routes a connected board offers.

    Args:
        grid: Maze to inspect.
        corridors: Cells of the corridor graph.

    Returns:
        The cyclomatic number of the corridor graph, which is zero for
        a perfect maze.
    """
    edges = sum(grid.degree(cell) for cell in corridors) // 2
    return edges - len(corridors) + 1


def has_open_area(grid: Grid) -> bool:
    """Return whether any 3x3 block of the maze is fully open.

    Args:
        grid: Maze to inspect.

    Returns:
        True when the twelve inner walls of some 3x3 block are open.
    """
    return any(
        _block_is_open(grid, (x, y))
        for y in range(grid.height - BLOCK_SIDE + 1)
        for x in range(grid.width - BLOCK_SIDE + 1)
    )


def creates_open_area(grid: Grid, source: Cell, target: Cell) -> bool:
    """Return whether opening a wall would open a whole 3x3 area.

    The wall is opened, the blocks covering both cells are inspected,
    then the wall is closed again, so the grid is left untouched.

    Args:
        grid: Maze the wall belongs to.
        source: First cell of the pair.
        target: Orthogonal neighbour of source, behind a closed wall.

    Returns:
        True when opening that wall would break the 3x3 rule.
    """
    grid.open_wall(source, target)
    found = any(
        _block_is_open(grid, origin)
        for origin in _blocks_covering(grid, source, target)
    )
    grid.close_wall(source, target)
    return found


def openable_neighbours(grid: Grid, cell: Cell) -> list[Cell]:
    """Return the neighbours a cell may safely be connected to.

    Args:
        grid: Maze to inspect.
        cell: Cell whose closed walls are candidates for opening.

    Returns:
        The corridor neighbours still behind a closed wall that may be
        opened without breaking the 3x3 rule.
    """
    return [
        other
        for other in grid.corridor_neighbours(cell)
        if not grid.is_open(cell, other)
        and not creates_open_area(grid, cell, other)
    ]


def openable_edges(
    grid: Grid,
    corridors: list[Cell],
) -> list[tuple[Cell, Cell]]:
    """Return every wall of the maze that may safely be opened.

    Args:
        grid: Maze to inspect.
        corridors: Cells of the corridor graph.

    Returns:
        The pairs of neighbouring corridor cells still separated by a
        wall that may be opened without breaking the 3x3 rule.
    """
    edges: list[tuple[Cell, Cell]] = []
    for cell in corridors:
        for other in grid.corridor_neighbours(cell):
            if other < cell or grid.is_open(cell, other):
                continue
            if not creates_open_area(grid, cell, other):
                edges.append((cell, other))
    return edges


def _blocks_covering(
    grid: Grid,
    source: Cell,
    target: Cell,
) -> list[Cell]:
    """Return the origins of the 3x3 blocks covering two cells."""
    low_x, high_x = sorted((source[0], target[0]))
    low_y, high_y = sorted((source[1], target[1]))
    return [
        (x, y)
        for y in range(
            max(0, high_y - BLOCK_SIDE + 1),
            min(low_y, grid.height - BLOCK_SIDE) + 1,
        )
        for x in range(
            max(0, high_x - BLOCK_SIDE + 1),
            min(low_x, grid.width - BLOCK_SIDE) + 1,
        )
    ]


def _block_is_open(grid: Grid, origin: Cell) -> bool:
    """Tell whether the twelve inner walls of a 3x3 block are open."""
    x, y = origin
    for row in range(BLOCK_SIDE):
        for column in range(BLOCK_SIDE - 1):
            first = (x + column, y + row)
            if not grid.is_open(first, (x + column + 1, y + row)):
                return False
    for row in range(BLOCK_SIDE - 1):
        for column in range(BLOCK_SIDE):
            first = (x + column, y + row)
            if not grid.is_open(first, (x + column, y + row + 1)):
                return False
    return True


def _check_endpoints(grid: Grid, entry: Cell, exit_: Cell) -> list[str]:
    """List the problems found on the entry and exit cells."""
    problems: list[str] = []
    for name, cell in (("entry", entry), ("exit", exit_)):
        if not grid.contains(cell):
            problems.append(f"the {name} lies outside the maze")
        elif grid.is_blocked(cell):
            problems.append(f"the {name} lies on the '42' pattern")
    if entry == exit_:
        problems.append("the entry and the exit are the same cell")
    return problems


def _check_sealed_cells(grid: Grid) -> list[str]:
    """List the cells of the "42" pattern that are not fully closed."""
    for cell in sorted(grid.blocked):
        if grid.walls(cell) != ALL_WALLS:
            return [f"the pattern cell {cell} is not fully closed"]
    return []


def _check_borders(grid: Grid) -> list[str]:
    """List the cells that open a hole in the outer border."""
    for y in range(grid.height):
        for x in range(grid.width):
            cell = (x, y)
            for bit in ORDER:
                if grid.walls(cell) & bit:
                    continue
                step = STEPS[bit]
                if not grid.contains((x + step[0], y + step[1])):
                    return [
                        f"the cell {cell} opens on the outer border"
                    ]
    return []


def _check_wall_coherence(grid: Grid) -> list[str]:
    """List the walls encoded differently by their two cells."""
    for y in range(grid.height):
        for x in range(grid.width):
            cell = (x, y)
            for other in ((x + 1, y), (x, y + 1)):
                if not grid.contains(other):
                    continue
                bit = grid.direction_between(cell, other)
                here = bool(grid.walls(cell) & bit)
                there = bool(grid.walls(other) & OPPOSITE[bit])
                if here != there:
                    return [
                        f"the wall between {cell} and {other} is "
                        "encoded differently by its two cells"
                    ]
    return []


def _check_perfect(grid: Grid, corridors: list[Cell]) -> list[str]:
    """List the problems of a maze that must hold a single path."""
    loops = loop_count(grid, corridors)
    if loops:
        return [f"a perfect maze must hold no loop, found {loops}"]
    return []


def _check_playable(grid: Grid, corridors: list[Cell]) -> list[str]:
    """List the problems of a maze that must be a playable board."""
    problems: list[str] = []
    loops = loop_count(grid, corridors)
    if loops < MIN_LOOPS:
        problems.append(
            f"a playable board needs {MIN_LOOPS} independent routes, "
            f"found {loops}"
        )
    for cell in _key_cells(grid):
        if grid.is_blocked(cell):
            problems.append(f"the key cell {cell} is not a corridor")
    dead_ends = sum(1 for cell in corridors if grid.degree(cell) == 1)
    if dead_ends > MAX_DEAD_ENDS:
        problems.append(
            f"a playable board tolerates {MAX_DEAD_ENDS} dead-ends, "
            f"found {dead_ends}"
        )
    return problems


def _key_cells(grid: Grid) -> tuple[Cell, ...]:
    """Return the four corners and the centre of the maze."""
    last_x = grid.width - 1
    last_y = grid.height - 1
    return (
        (0, 0),
        (last_x, 0),
        (0, last_y),
        (last_x, last_y),
        (grid.width // 2, grid.height // 2),
    )


def _reachable(grid: Grid, start: Cell) -> set[Cell]:
    """Return every corridor cell reachable from a starting cell."""
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for other in grid.open_neighbours(cell):
            if other not in seen:
                seen.add(other)
                queue.append(other)
    return seen
