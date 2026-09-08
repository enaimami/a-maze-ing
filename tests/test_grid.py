"""Check the wall bookkeeping of the Grid class."""

import unittest

from mazegen.grid import ALL_WALLS, EAST, NORTH, SOUTH, WEST, Grid


class GridTest(unittest.TestCase):
    """Check that walls stay coherent whatever is done to them."""

    def test_starts_fully_closed(self) -> None:
        """Every cell of a fresh grid has its four walls closed."""
        grid = Grid(4, 3)
        for cell in grid.corridors():
            self.assertEqual(grid.walls(cell), ALL_WALLS)

    def test_refuses_a_degenerate_size(self) -> None:
        """A grid narrower or shorter than two cells is refused."""
        with self.assertRaises(ValueError):
            Grid(1, 5)

    def test_opening_updates_both_cells(self) -> None:
        """Opening a wall clears the matching bit on both neighbours."""
        grid = Grid(3, 3)
        grid.open_wall((0, 0), (1, 0))
        self.assertFalse(grid.walls((0, 0)) & EAST)
        self.assertFalse(grid.walls((1, 0)) & WEST)
        self.assertTrue(grid.is_open((1, 0), (0, 0)))

    def test_closing_restores_both_cells(self) -> None:
        """Closing a wall sets the matching bit on both neighbours."""
        grid = Grid(3, 3)
        grid.open_wall((1, 1), (1, 2))
        grid.close_wall((1, 1), (1, 2))
        self.assertTrue(grid.walls((1, 1)) & SOUTH)
        self.assertTrue(grid.walls((1, 2)) & NORTH)

    def test_refuses_a_wall_between_strangers(self) -> None:
        """Only orthogonal neighbours share a wall."""
        grid = Grid(3, 3)
        with self.assertRaises(ValueError):
            grid.open_wall((0, 0), (2, 2))

    def test_blocking_seals_a_cell(self) -> None:
        """A blocked cell leaves the corridors with all walls closed."""
        grid = Grid(3, 3)
        grid.open_wall((1, 1), (1, 0))
        grid.block((1, 1))
        self.assertEqual(grid.walls((1, 1)), ALL_WALLS)
        self.assertEqual(grid.walls((1, 0)), ALL_WALLS)
        self.assertNotIn((1, 1), grid.corridors())
        self.assertIn((1, 1), grid.blocked)

    def test_hexadecimal_encoding_is_lowercase(self) -> None:
        """Rows are encoded as one lowercase digit per cell."""
        grid = Grid(2, 2)
        self.assertEqual(grid.to_hex_lines(), ["ff", "ff"])
        grid.open_wall((0, 0), (1, 0))
        self.assertEqual(grid.to_hex_lines()[0], "d7")

    def test_snapshot_is_independent(self) -> None:
        """Changing a snapshot leaves the grid untouched."""
        grid = Grid(2, 2)
        snapshot = grid.snapshot()
        snapshot[0][0] = 0
        self.assertEqual(grid.walls((0, 0)), ALL_WALLS)


if __name__ == "__main__":
    unittest.main()
