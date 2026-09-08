"""Check that generated mazes honour every rule of the subject."""

import unittest
from collections import deque

from mazegen import (
    InvalidParametersError,
    MazeError,
    MazeGenerationError,
    MazeGenerator,
)
from mazegen.grid import EAST, NORTH, SOUTH, STEPS, WEST

Cell = tuple[int, int]

SIZES = ((10, 10), (12, 9), (20, 15), (25, 20), (31, 17))


def _build(width: int, height: int, perfect: bool, seed: int) -> MazeGenerator:
    """Return a freshly generated maze spanning a whole board."""
    generator = MazeGenerator(
        width=width,
        height=height,
        entry=(0, 0),
        exit_=(width - 1, height - 1),
        perfect=perfect,
        seed=seed,
    )
    generator.generate()
    return generator


def _neighbours(cells: list[list[int]], cell: Cell) -> list[Cell]:
    """Return the cells reachable from a cell without crossing a wall."""
    height = len(cells)
    width = len(cells[0])
    reachable = []
    for bit in (NORTH, EAST, SOUTH, WEST):
        step = STEPS[bit]
        other = (cell[0] + step[0], cell[1] + step[1])
        if not 0 <= other[0] < width or not 0 <= other[1] < height:
            continue
        if not cells[cell[1]][cell[0]] & bit:
            reachable.append(other)
    return reachable


class GeneratorTest(unittest.TestCase):
    """Check the invariants shared by both generation modes."""

    def test_refuses_a_degenerate_board(self) -> None:
        """A board narrower than two cells is refused."""
        with self.assertRaises(InvalidParametersError):
            MazeGenerator(1, 10, (0, 0), (0, 9))

    def test_refuses_an_endpoint_outside_the_board(self) -> None:
        """An exit outside the board is refused."""
        with self.assertRaises(InvalidParametersError):
            MazeGenerator(10, 10, (0, 0), (10, 0))

    def test_refuses_twin_endpoints(self) -> None:
        """An exit equal to the entry is refused."""
        with self.assertRaises(InvalidParametersError):
            MazeGenerator(10, 10, (2, 2), (2, 2))

    def test_refuses_an_impossible_board(self) -> None:
        """A two by two playable board cannot offer two routes."""
        with self.assertRaises(MazeGenerationError):
            _build(2, 2, False, 1)

    def test_refuses_to_answer_before_generating(self) -> None:
        """Reading a maze that was never generated is refused."""
        generator = MazeGenerator(10, 10, (0, 0), (9, 9))
        with self.assertRaises(MazeError):
            generator.solution()

    def test_the_same_seed_rebuilds_the_same_maze(self) -> None:
        """Two runs sharing a seed produce the very same board."""
        first = _build(20, 15, False, 42)
        second = _build(20, 15, False, 42)
        self.assertEqual(first.to_hex_lines(), second.to_hex_lines())
        self.assertEqual(
            first.solution_directions(), second.solution_directions()
        )

    def test_another_seed_builds_another_maze(self) -> None:
        """Two runs with different seeds produce different boards."""
        first = _build(20, 15, False, 42)
        second = _build(20, 15, False, 43)
        self.assertNotEqual(first.to_hex_lines(), second.to_hex_lines())

    def test_walls_agree_on_both_sides(self) -> None:
        """Neighbouring cells always encode their shared wall alike."""
        for width, height in SIZES:
            cells = _build(width, height, False, 3).cells
            for y in range(height):
                for x in range(width):
                    if x + 1 < width:
                        here = bool(cells[y][x] & EAST)
                        there = bool(cells[y][x + 1] & WEST)
                        self.assertEqual(here, there, (x, y))
                    if y + 1 < height:
                        here = bool(cells[y][x] & SOUTH)
                        there = bool(cells[y + 1][x] & NORTH)
                        self.assertEqual(here, there, (x, y))

    def test_the_outer_border_stays_closed(self) -> None:
        """No cell opens a hole through the outer border."""
        for width, height in SIZES:
            cells = _build(width, height, False, 5).cells
            for x in range(width):
                self.assertTrue(cells[0][x] & NORTH)
                self.assertTrue(cells[height - 1][x] & SOUTH)
            for y in range(height):
                self.assertTrue(cells[y][0] & WEST)
                self.assertTrue(cells[y][width - 1] & EAST)

    def test_no_area_of_three_by_three_is_fully_open(self) -> None:
        """Corridors never widen into a three by three open area."""
        for width, height in SIZES:
            for perfect in (True, False):
                cells = _build(width, height, perfect, 9).cells
                for y in range(height - 2):
                    for x in range(width - 2):
                        walls = [
                            cells[y + row][x + column] & EAST
                            for row in range(3)
                            for column in range(2)
                        ] + [
                            cells[y + row][x + column] & SOUTH
                            for row in range(2)
                            for column in range(3)
                        ]
                        self.assertTrue(any(walls), (x, y))

    def test_the_pattern_cells_are_fully_closed(self) -> None:
        """Every cell of the "42" keeps its four walls."""
        generator = _build(20, 15, False, 11)
        cells = generator.cells
        self.assertTrue(generator.pattern_cells)
        for x, y in generator.pattern_cells:
            self.assertEqual(cells[y][x], NORTH | EAST | SOUTH | WEST)

    def test_the_solution_walks_the_maze(self) -> None:
        """The solution letters match the cells of the solution path."""
        for perfect in (True, False):
            generator = _build(20, 15, perfect, 13)
            path = generator.solution()
            letters = generator.solution_directions()
            self.assertEqual(len(letters), len(path) - 1)
            self.assertEqual(path[0], (0, 0))
            self.assertEqual(path[-1], (19, 14))
            cells = generator.cells
            for index in range(len(path) - 1):
                self.assertIn(path[index + 1], _neighbours(cells, path[index]))

    def test_the_solution_is_the_shortest_one(self) -> None:
        """No walk reaches the exit in fewer steps than the solution."""
        generator = _build(20, 15, False, 17)
        cells = generator.cells
        distance = {(0, 0): 0}
        queue = deque([(0, 0)])
        while queue:
            cell = queue.popleft()
            for other in _neighbours(cells, cell):
                if other not in distance:
                    distance[other] = distance[cell] + 1
                    queue.append(other)
        self.assertEqual(
            distance[(19, 14)], len(generator.solution_directions())
        )


class PerfectMazeTest(unittest.TestCase):
    """Check the rules that only apply to perfect mazes."""

    def test_a_perfect_maze_is_a_spanning_tree(self) -> None:
        """Corridors hold exactly one open wall less than cells."""
        for width, height in SIZES:
            generator = _build(width, height, True, 21)
            cells = generator.cells
            corridors = [
                (x, y)
                for y in range(height)
                for x in range(width)
                if (x, y) not in generator.pattern_cells
            ]
            edges = sum(
                len(_neighbours(cells, cell)) for cell in corridors
            ) // 2
            self.assertEqual(edges, len(corridors) - 1)


class PlayableBoardTest(unittest.TestCase):
    """Check the rules that only apply to playable boards."""

    def test_a_playable_board_offers_two_routes(self) -> None:
        """Corridors hold at least two independent loops."""
        for width, height in SIZES:
            generator = _build(width, height, False, 23)
            cells = generator.cells
            corridors = [
                (x, y)
                for y in range(height)
                for x in range(width)
                if (x, y) not in generator.pattern_cells
            ]
            edges = sum(
                len(_neighbours(cells, cell)) for cell in corridors
            ) // 2
            self.assertGreaterEqual(edges - len(corridors) + 1, 2)

    def test_a_playable_board_has_no_dead_end(self) -> None:
        """Braiding removes every dead-end of the board."""
        for width, height in SIZES:
            for seed in range(4):
                generator = _build(width, height, False, seed)
                cells = generator.cells
                dead_ends = [
                    (x, y)
                    for y in range(height)
                    for x in range(width)
                    if (x, y) not in generator.pattern_cells
                    and len(_neighbours(cells, (x, y))) == 1
                ]
                self.assertEqual(dead_ends, [], (width, height, seed))

    def test_a_playable_board_keeps_its_key_cells(self) -> None:
        """The four corners and the centre stay open corridors."""
        for width, height in SIZES:
            generator = _build(width, height, False, 27)
            for cell in (
                (0, 0),
                (width - 1, 0),
                (0, height - 1),
                (width - 1, height - 1),
                (width // 2, height // 2),
            ):
                self.assertNotIn(cell, generator.pattern_cells)


if __name__ == "__main__":
    unittest.main()
