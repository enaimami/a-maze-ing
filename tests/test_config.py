"""Check the strict parsing of the configuration file."""

import tempfile
import unittest
from pathlib import Path

from app.config import ConfigError, load_config

VALID = (
    "# a comment\n"
    "\n"
    "WIDTH=20\n"
    "HEIGHT=15\n"
    "ENTRY=0,0\n"
    "EXIT=19,14\n"
    "OUTPUT_FILE=maze.txt\n"
    "PERFECT=False\n"
    "SEED=42\n"
)


class ConfigTest(unittest.TestCase):
    """Check that only well formed configurations are accepted."""

    def setUp(self) -> None:
        """Create a temporary directory for the configuration files."""
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)

    def _write(self, text: str) -> str:
        """Write a configuration file and return its path."""
        path = Path(self._directory.name) / "config.txt"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def _refuse(self, text: str) -> str:
        """Load a configuration expected to fail and return the message."""
        with self.assertRaises(ConfigError) as caught:
            load_config(self._write(text))
        return str(caught.exception)

    def test_reads_a_valid_file(self) -> None:
        """A complete configuration is parsed into its values."""
        config = load_config(self._write(VALID))
        self.assertEqual(config.width, 20)
        self.assertEqual(config.height, 15)
        self.assertEqual(config.entry, (0, 0))
        self.assertEqual(config.exit_, (19, 14))
        self.assertEqual(config.output_file, "maze.txt")
        self.assertFalse(config.perfect)
        self.assertEqual(config.seed, 42)

    def test_the_seed_is_optional(self) -> None:
        """A file without a seed leaves the seed undecided."""
        config = load_config(self._write(VALID.replace("SEED=42\n", "")))
        self.assertIsNone(config.seed)

    def test_reads_a_boolean_whatever_its_case(self) -> None:
        """The perfect flag is not case sensitive."""
        config = load_config(
            self._write(VALID.replace("PERFECT=False", "PERFECT=tRuE"))
        )
        self.assertTrue(config.perfect)

    def test_refuses_a_missing_file(self) -> None:
        """A path that leads nowhere is reported as unreadable."""
        with self.assertRaises(ConfigError):
            load_config(str(Path(self._directory.name) / "absent.txt"))

    def test_refuses_a_missing_key(self) -> None:
        """A mandatory key that is absent is reported by its name."""
        message = self._refuse(VALID.replace("PERFECT=False\n", ""))
        self.assertIn("PERFECT", message)

    def test_refuses_an_unknown_key(self) -> None:
        """A key outside of the format is refused, not ignored."""
        message = self._refuse(VALID + "ALGORITHM=dfs\n")
        self.assertIn("unknown key", message)

    def test_refuses_a_repeated_key(self) -> None:
        """A key written twice is refused."""
        message = self._refuse(VALID + "WIDTH=30\n")
        self.assertIn("duplicate key", message)

    def test_refuses_a_line_without_separator(self) -> None:
        """A line holding no equal sign is refused."""
        message = self._refuse(VALID + "BROKEN\n")
        self.assertIn("separator", message)

    def test_refuses_a_size_that_is_not_a_number(self) -> None:
        """A size written in letters is refused."""
        message = self._refuse(VALID.replace("WIDTH=20", "WIDTH=wide"))
        self.assertIn("integer", message)

    def test_refuses_a_size_below_two(self) -> None:
        """A board narrower than two cells is refused."""
        message = self._refuse(VALID.replace("WIDTH=20", "WIDTH=1"))
        self.assertIn("at least 2", message)

    def test_refuses_an_endpoint_outside_the_board(self) -> None:
        """An exit outside the board is refused."""
        message = self._refuse(VALID.replace("EXIT=19,14", "EXIT=20,14"))
        self.assertIn("outside", message)

    def test_refuses_twin_endpoints(self) -> None:
        """An exit equal to the entry is refused."""
        message = self._refuse(VALID.replace("EXIT=19,14", "EXIT=0,0"))
        self.assertIn("different", message)

    def test_refuses_a_malformed_cell(self) -> None:
        """A coordinate pair without a comma is refused."""
        message = self._refuse(VALID.replace("ENTRY=0,0", "ENTRY=0"))
        self.assertIn("'x,y'", message)

    def test_refuses_an_empty_output_file(self) -> None:
        """An output path left empty is refused."""
        message = self._refuse(
            VALID.replace("OUTPUT_FILE=maze.txt", "OUTPUT_FILE=")
        )
        self.assertIn("OUTPUT_FILE", message)

    def test_refuses_a_broken_boolean(self) -> None:
        """A perfect flag that is neither true nor false is refused."""
        message = self._refuse(VALID.replace("PERFECT=False", "PERFECT=1"))
        self.assertIn("True or False", message)


if __name__ == "__main__":
    unittest.main()
