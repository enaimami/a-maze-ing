"""Build mazes that honour every rule of the subject."""

import random

from mazegen.errors import (
    InvalidParametersError,
    MazeError,
    MazeGenerationError,
)
from mazegen.grid import Cell, Grid
from mazegen.pattern import place_pattern
from mazegen.solver import directions_of, shortest_path
from mazegen.validator import (
    MIN_LOOPS,
    loop_count,
    openable_edges,
    openable_neighbours,
    validate,
)

MIN_SIDE = 2
SEED_BITS = 32

Steps = list[tuple[Cell, Cell]]


class MazeGenerator:
    """Generate a maze, its "42" pattern and its shortest path."""

    MAX_ATTEMPTS = 32
    MAX_BRAID_PASSES = 8

    def __init__(
        self,
        width: int,
        height: int,
        entry: Cell,
        exit_: Cell,
        perfect: bool = False,
        seed: int | None = None,
    ) -> None:
        """Store the parameters of a maze without generating it yet.

        Args:
            width: Number of cells along the horizontal axis.
            height: Number of cells along the vertical axis.
            entry: Cell the player enters from.
            exit_: Cell the player leaves from.
            perfect: Whether a single path between entry and exit is
                wanted instead of a playable braided board.
            seed: Seed making the generation reproducible. A random one
                is drawn when it is omitted.

        Raises:
            InvalidParametersError: If the maze is too small, if an
                endpoint lies outside of it or if both endpoints are
                the same cell.
        """
        if width < MIN_SIDE or height < MIN_SIDE:
            raise InvalidParametersError(
                f"a maze must be at least {MIN_SIDE}x{MIN_SIDE} cells"
            )
        for name, cell in (("entry", entry), ("exit", exit_)):
            if not 0 <= cell[0] < width or not 0 <= cell[1] < height:
                raise InvalidParametersError(
                    f"the {name} {cell} lies outside the maze"
                )
        if entry == exit_:
            raise InvalidParametersError(
                "the entry and the exit must be different cells"
            )
        self._width = width
        self._height = height
        self._entry = entry
        self._exit = exit_
        self._perfect = perfect
        self._seed = (
            random.Random().getrandbits(SEED_BITS) if seed is None else seed
        )
        self._grid: Grid | None = None
        self._path: list[Cell] = []
        self._steps: Steps = []

    @property
    def seed(self) -> int:
        """Return the seed the generation is reproducible with."""
        return self._seed

    @property
    def cells(self) -> list[list[int]]:
        """Return the wall bits of every cell, row by row.

        Returns:
            One list of packed wall bits per row of the maze.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        return self._built().snapshot()

    @property
    def pattern_cells(self) -> frozenset[Cell]:
        """Return the fully closed cells drawing the "42" pattern.

        Returns:
            The sealed cells, empty when the maze was too small or too
            constrained to host the pattern.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        return self._built().blocked

    def generate(self) -> None:
        """Build a maze matching the requested mode.

        A depth-first spanning tree is carved over the cells left free
        by the "42" pattern, then braided into loops when a playable
        board is wanted. Every failed attempt restarts from a derived
        seed.

        Raises:
            MazeGenerationError: If no attempt produced a valid maze.
        """
        problems = ["the requested parameters allow no valid maze"]
        for attempt in range(self.MAX_ATTEMPTS):
            rng = random.Random(self._seed + attempt)
            grid = Grid(self._width, self._height)
            steps: Steps = []
            for cell in sorted(
                place_pattern(self._width, self._height, self._forbidden())
            ):
                grid.block(cell)
            self._carve(grid, rng, steps)
            if not self._perfect:
                self._braid(grid, rng, steps)
            problems = validate(grid, self._entry, self._exit, self._perfect)
            if problems:
                continue
            path = shortest_path(grid, self._entry, self._exit)
            if path is None:
                problems = ["no path links the entry to the exit"]
                continue
            self._grid = grid
            self._path = path
            self._steps = steps
            return
        raise MazeGenerationError(
            f"no valid maze after {self.MAX_ATTEMPTS} attempts "
            f"({problems[0]})"
        )

    def solution(self) -> list[Cell]:
        """Return the shortest path, entry and exit included.

        Returns:
            The consecutive cells walked from the entry to the exit.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        self._built()
        return list(self._path)

    def solution_directions(self) -> str:
        """Return the shortest path as N, E, S and W letters.

        Returns:
            One letter per step walked from the entry to the exit.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        return directions_of(self._built(), self._path)

    def build_steps(self) -> Steps:
        """Return the walls opened while building, in the right order.

        Each pair holds the two cells whose shared wall was opened,
        first by the depth-first carving, then by the braiding when a
        playable board was asked for. Replaying them on a grid that
        only holds the pattern cells rebuilds the maze wall by wall,
        which is what an animation of the generation needs.

        Returns:
            The pairs of neighbouring cells whose shared wall was
            opened, in the order the generation opened them.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        self._built()
        return list(self._steps)

    def to_hex_lines(self) -> list[str]:
        """Return one lowercase hexadecimal line per row of cells.

        Returns:
            The rows of the maze encoded as in the output file.

        Raises:
            MazeError: If the maze has not been generated yet.
        """
        return self._built().to_hex_lines()

    def _built(self) -> Grid:
        """Return the generated grid, or refuse to work without one."""
        if self._grid is None:
            raise MazeError("generate() must be called first")
        return self._grid

    def _forbidden(self) -> frozenset[Cell]:
        """Return the cells the "42" pattern may never cover."""
        last_x = self._width - 1
        last_y = self._height - 1
        return frozenset(
            {
                self._entry,
                self._exit,
                (0, 0),
                (last_x, 0),
                (0, last_y),
                (last_x, last_y),
                (self._width // 2, self._height // 2),
            }
        )

    def _carve(self, grid: Grid, rng: random.Random, steps: Steps) -> None:
        """Carve a spanning tree over the corridor cells of a grid."""
        stack = [self._entry]
        visited = {self._entry}
        while stack:
            cell = stack[-1]
            candidates = [
                other
                for other in grid.corridor_neighbours(cell)
                if other not in visited
            ]
            if not candidates:
                stack.pop()
                continue
            rng.shuffle(candidates)
            chosen = candidates[0]
            grid.open_wall(cell, chosen)
            steps.append((cell, chosen))
            visited.add(chosen)
            stack.append(chosen)

    def _braid(self, grid: Grid, rng: random.Random, steps: Steps) -> None:
        """Remove the dead-ends of a grid, then secure its loops."""
        for _ in range(self.MAX_BRAID_PASSES):
            dead_ends = [
                cell for cell in grid.corridors() if grid.degree(cell) == 1
            ]
            if not dead_ends:
                break
            rng.shuffle(dead_ends)
            opened = False
            for cell in dead_ends:
                if grid.degree(cell) != 1:
                    continue
                candidates = openable_neighbours(grid, cell)
                if not candidates:
                    continue
                rng.shuffle(candidates)
                candidates.sort(key=grid.degree)
                grid.open_wall(cell, candidates[0])
                steps.append((cell, candidates[0]))
                opened = True
            if not opened:
                break
        self._add_loops(grid, rng, steps)

    @staticmethod
    def _add_loops(grid: Grid, rng: random.Random, steps: Steps) -> None:
        """Open extra walls until the board offers enough routes."""
        corridors = grid.corridors()
        while loop_count(grid, corridors) < MIN_LOOPS:
            candidates = openable_edges(grid, corridors)
            if not candidates:
                return
            source, target = rng.choice(candidates)
            grid.open_wall(source, target)
            steps.append((source, target))
