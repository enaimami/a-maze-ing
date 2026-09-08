"""Store the wall bits of a maze and own every wall mutation."""

Cell = tuple[int, int]

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
ALL_WALLS = NORTH | EAST | SOUTH | WEST

STEPS: dict[int, Cell] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

LETTERS: dict[int, str] = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}

ORDER: tuple[int, ...] = (NORTH, EAST, SOUTH, WEST)


class Grid:
    """Hold the wall bits of every cell of a rectangular maze."""

    def __init__(self, width: int, height: int) -> None:
        """Create a grid whose cells all have their four walls closed.

        Args:
            width: Number of cells along the horizontal axis.
            height: Number of cells along the vertical axis.

        Raises:
            ValueError: If width or height is smaller than two.
        """
        if width < 2 or height < 2:
            raise ValueError("a grid must be at least 2x2 cells")
        self._width = width
        self._height = height
        self._cells: list[list[int]] = [
            [ALL_WALLS] * width for _ in range(height)
        ]
        self._blocked: set[Cell] = set()

    @property
    def width(self) -> int:
        """Return the number of cells along the horizontal axis."""
        return self._width

    @property
    def height(self) -> int:
        """Return the number of cells along the vertical axis."""
        return self._height

    @property
    def blocked(self) -> frozenset[Cell]:
        """Return the cells kept outside of the corridor graph."""
        return frozenset(self._blocked)

    def snapshot(self) -> list[list[int]]:
        """Return an independent copy of the wall bits, row by row."""
        return [list(row) for row in self._cells]

    def contains(self, cell: Cell) -> bool:
        """Return whether a coordinate pair lies inside the grid.

        Args:
            cell: Coordinate pair to test.

        Returns:
            True when the cell is inside the grid bounds.
        """
        x, y = cell
        return 0 <= x < self._width and 0 <= y < self._height

    def is_blocked(self, cell: Cell) -> bool:
        """Return whether a cell is excluded from the corridor graph.

        Args:
            cell: Coordinate pair to test.

        Returns:
            True when the cell belongs to the blocked set.
        """
        return cell in self._blocked

    def walls(self, cell: Cell) -> int:
        """Return the wall bits of a cell.

        Args:
            cell: Coordinate pair to read.

        Returns:
            The four wall bits packed in a single integer.

        Raises:
            ValueError: If the cell lies outside the grid.
        """
        self._require_inside(cell)
        return self._cells[cell[1]][cell[0]]

    def direction_between(self, source: Cell, target: Cell) -> int:
        """Return the wall bit of source that faces target.

        Args:
            source: Cell the wall belongs to.
            target: Orthogonal neighbour behind that wall.

        Returns:
            One of the NORTH, EAST, SOUTH or WEST bits.

        Raises:
            ValueError: If the cells are not orthogonal neighbours.
        """
        delta = (target[0] - source[0], target[1] - source[1])
        for bit in ORDER:
            if STEPS[bit] == delta:
                return bit
        raise ValueError(f"{source} and {target} are not neighbours")

    def neighbours(self, cell: Cell) -> list[Cell]:
        """Return the in-bounds orthogonal neighbours of a cell.

        Args:
            cell: Coordinate pair to inspect.

        Returns:
            The neighbouring cells in north, east, south, west order.
        """
        x, y = cell
        found: list[Cell] = []
        for bit in ORDER:
            step = STEPS[bit]
            candidate = (x + step[0], y + step[1])
            if self.contains(candidate):
                found.append(candidate)
        return found

    def corridor_neighbours(self, cell: Cell) -> list[Cell]:
        """Return the in-bounds neighbours that are not blocked.

        Args:
            cell: Coordinate pair to inspect.

        Returns:
            The neighbouring cells that belong to the corridor graph.
        """
        return [
            other
            for other in self.neighbours(cell)
            if not self.is_blocked(other)
        ]

    def is_open(self, source: Cell, target: Cell) -> bool:
        """Return whether the wall shared by two neighbours is open.

        Args:
            source: First cell of the pair.
            target: Orthogonal neighbour of source.

        Returns:
            True when the shared wall bit of source is cleared.

        Raises:
            ValueError: If the cells are not orthogonal neighbours.
        """
        bit = self.direction_between(source, target)
        return not self.walls(source) & bit

    def open_neighbours(self, cell: Cell) -> list[Cell]:
        """Return the neighbours reachable from a cell without a wall.

        Args:
            cell: Coordinate pair to inspect.

        Returns:
            The neighbouring cells whose shared wall is open.
        """
        return [
            other
            for other in self.neighbours(cell)
            if self.is_open(cell, other)
        ]

    def degree(self, cell: Cell) -> int:
        """Return how many open walls a cell has.

        Args:
            cell: Coordinate pair to inspect.

        Returns:
            The number of neighbours reachable without crossing a wall.
        """
        return len(self.open_neighbours(cell))

    def corridors(self) -> list[Cell]:
        """Return every cell of the corridor graph in row-major order."""
        return [
            (x, y)
            for y in range(self._height)
            for x in range(self._width)
            if (x, y) not in self._blocked
        ]

    def open_wall(self, source: Cell, target: Cell) -> None:
        """Clear the wall shared by two neighbouring cells.

        Args:
            source: First cell of the pair.
            target: Orthogonal neighbour of source.

        Raises:
            ValueError: If the cells are not orthogonal neighbours or
                if either of them lies outside the grid.
        """
        bit = self.direction_between(source, target)
        self._require_inside(source)
        self._require_inside(target)
        self._cells[source[1]][source[0]] &= ~bit
        self._cells[target[1]][target[0]] &= ~OPPOSITE[bit]

    def close_wall(self, source: Cell, target: Cell) -> None:
        """Set the wall shared by two neighbouring cells.

        Args:
            source: First cell of the pair.
            target: Orthogonal neighbour of source.

        Raises:
            ValueError: If the cells are not orthogonal neighbours or
                if either of them lies outside the grid.
        """
        bit = self.direction_between(source, target)
        self._require_inside(source)
        self._require_inside(target)
        self._cells[source[1]][source[0]] |= bit
        self._cells[target[1]][target[0]] |= OPPOSITE[bit]

    def block(self, cell: Cell) -> None:
        """Seal a cell and exclude it from the corridor graph.

        Args:
            cell: Coordinate pair to seal.

        Raises:
            ValueError: If the cell lies outside the grid.
        """
        self._require_inside(cell)
        for other in self.neighbours(cell):
            self.close_wall(cell, other)
        self._blocked.add(cell)

    def to_hex_lines(self) -> list[str]:
        """Return one lowercase hexadecimal line per row of cells."""
        return [
            "".join(f"{value:x}" for value in row) for row in self._cells
        ]

    def _require_inside(self, cell: Cell) -> None:
        """Refuse to work on a cell that lies outside the grid."""
        if not self.contains(cell):
            raise ValueError(f"{cell} is outside the grid")
