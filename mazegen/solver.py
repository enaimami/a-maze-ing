"""Find the shortest path between two cells of a maze."""

from collections import deque

from mazegen.grid import Cell, Grid, LETTERS


def shortest_path(grid: Grid, start: Cell, goal: Cell) -> list[Cell] | None:
    """Return the shortest corridor path between two cells.

    The walk is a breadth-first search over an explicit queue, so the
    result is the shortest path in number of cells and the search never
    relies on recursion.

    Args:
        grid: Maze to walk through.
        start: Cell the path starts from.
        goal: Cell the path ends on.

    Returns:
        The cells of the path from start to goal, or None when the goal
        cannot be reached.

    Raises:
        ValueError: If start or goal lies outside the grid.
    """
    if not grid.contains(start) or not grid.contains(goal):
        raise ValueError("start and goal must be inside the grid")
    if grid.is_blocked(start) or grid.is_blocked(goal):
        return None
    previous: dict[Cell, Cell] = {}
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            return _rebuild(previous, start, goal)
        for other in grid.open_neighbours(cell):
            if other not in seen:
                seen.add(other)
                previous[other] = cell
                queue.append(other)
    return None


def directions_of(grid: Grid, path: list[Cell]) -> str:
    """Return the cardinal letters walked along a path.

    Args:
        grid: Maze the path belongs to.
        path: Consecutive cells, as returned by shortest_path.

    Returns:
        A string made of the letters N, E, S and W.

    Raises:
        ValueError: If two consecutive cells are not neighbours.
    """
    letters = []
    for index in range(len(path) - 1):
        bit = grid.direction_between(path[index], path[index + 1])
        letters.append(LETTERS[bit])
    return "".join(letters)


def _rebuild(
    previous: dict[Cell, Cell],
    start: Cell,
    goal: Cell,
) -> list[Cell]:
    """Return the path stored in a breadth-first predecessor map."""
    path = [goal]
    cell = goal
    while cell != start:
        cell = previous[cell]
        path.append(cell)
    path.reverse()
    return path
