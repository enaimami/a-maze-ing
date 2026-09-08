"""Check where the "42" pattern is allowed to be stamped."""

import unittest

from mazegen.pattern import PATTERN_42, MARK, place_pattern, pattern_size


def _free(width: int, height: int) -> frozenset[tuple[int, int]]:
    """Return the cells the pattern may never cover on a board."""
    return frozenset(
        {
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),
            (width // 2, height // 2),
        }
    )


class PatternTest(unittest.TestCase):
    """Check the bitmap and the placement rules of the pattern."""

    def test_bitmap_is_rectangular(self) -> None:
        """Every row of the bitmap has the same length."""
        width, height = pattern_size()
        self.assertEqual(height, len(PATTERN_42))
        for row in PATTERN_42:
            self.assertEqual(len(row), width)

    def test_a_small_board_gets_no_pattern(self) -> None:
        """A board smaller than the bitmap hosts no pattern."""
        self.assertEqual(place_pattern(5, 5, _free(5, 5)), frozenset())

    def test_a_large_board_gets_the_whole_pattern(self) -> None:
        """A roomy board hosts every marked cell of the bitmap."""
        marks = sum(row.count(MARK) for row in PATTERN_42)
        self.assertEqual(len(place_pattern(20, 15, _free(20, 15))), marks)

    def test_the_pattern_spares_the_key_cells(self) -> None:
        """Corners, centre and endpoints stay outside the pattern."""
        for width in range(9, 26):
            for height in range(9, 21):
                forbidden = _free(width, height)
                cells = place_pattern(width, height, forbidden)
                self.assertFalse(cells & forbidden, (width, height))

    def test_the_pattern_keeps_two_neighbours_everywhere(self) -> None:
        """No corridor cell is left with a single corridor neighbour."""
        width, height = 20, 15
        cells = place_pattern(width, height, _free(width, height))
        self.assertTrue(cells)
        for y in range(height):
            for x in range(width):
                if (x, y) in cells:
                    continue
                around = [
                    (x + dx, y + dy)
                    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))
                ]
                free = [
                    cell
                    for cell in around
                    if 0 <= cell[0] < width
                    and 0 <= cell[1] < height
                    and cell not in cells
                ]
                self.assertGreaterEqual(len(free), 2, (x, y))

    def test_placement_is_reproducible(self) -> None:
        """The same board always receives the pattern at the same place."""
        first = place_pattern(20, 15, _free(20, 15))
        second = place_pattern(20, 15, _free(20, 15))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
