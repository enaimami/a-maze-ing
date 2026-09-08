"""Check the layout of the output file."""

import tempfile
import unittest
from pathlib import Path

from app.writer import write_maze
from mazegen import MazeGenerator


class WriterTest(unittest.TestCase):
    """Check that the output file follows the format of the subject."""

    def setUp(self) -> None:
        """Create a temporary directory for the output files."""
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)

    def test_writes_the_expected_layout(self) -> None:
        """Rows come first, then a blank line, then the three answers."""
        generator = MazeGenerator(20, 15, (0, 0), (19, 14), False, 42)
        generator.generate()
        path = str(Path(self._directory.name) / "maze.txt")
        write_maze(
            path,
            generator.to_hex_lines(),
            (0, 0),
            (19, 14),
            generator.solution_directions(),
        )
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith("\n"))
        lines = raw.split("\n")[:-1]
        self.assertEqual(len(lines), 15 + 1 + 3)
        for row in lines[:15]:
            self.assertEqual(len(row), 20)
            self.assertEqual(row, row.lower())
            self.assertTrue(all(digit in "0123456789abcdef" for digit in row))
        self.assertEqual(lines[15], "")
        self.assertEqual(lines[16], "0,0")
        self.assertEqual(lines[17], "19,14")
        self.assertTrue(set(lines[18]) <= set("NESW"))

    def test_reports_an_unwritable_path(self) -> None:
        """A path that cannot be created is reported as an error."""
        path = str(Path(self._directory.name) / "absent" / "maze.txt")
        with self.assertRaises(OSError):
            write_maze(path, ["ff"], (0, 0), (1, 1), "SE")


if __name__ == "__main__":
    unittest.main()
