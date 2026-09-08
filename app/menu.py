"""Run the interactive session that displays and rebuilds the maze."""

import random
import sys

from app.config import MazeConfig
from app.renderer import (
    WALL_PALETTE,
    animate_build,
    animate_path,
    render,
)
from app.writer import write_maze
from mazegen import MazeGenerator

TITLE = "=== A-Maze-ing ==="
ENTRIES = (
    "1. Re-generate a new maze",
    "2. Show / Hide the shortest path",
    "3. Rotate the wall colours",
    "4. Toggle the animations",
    "5. Quit",
)
CHOICES = ("1", "2", "3", "4", "5")
PROMPT = "Choice? (1-5): "
INVALID = "Please answer with a number between 1 and 5."
NO_PATTERN = "Error: the maze is too small to draw the '42' pattern"
SEED_NOTICE = "Generated seed: {seed}"
BUILD = "build"
SOLVE = "solve"
SEED_BITS = 32


class MazeSession:
    """Keep the state of one interactive run of the program."""

    def __init__(self, config: MazeConfig) -> None:
        """Generate a first maze and prepare the interactive state.

        Args:
            config: Validated content of the configuration file.

        Raises:
            MazeError: If no maze matching the configuration exists.
            OSError: If the output file cannot be written.
        """
        seed = config.seed
        if seed is None:
            seed = random.Random().getrandbits(SEED_BITS)
            print(SEED_NOTICE.format(seed=seed))
        self._config = config
        self._rng = random.Random(seed)
        self._show_path = False
        self._animate = True
        self._palette = 0
        self._pending: str | None = BUILD
        self._generator = self._build(seed)

    def run(self) -> None:
        """Display the maze and serve the menu until the user leaves.

        Raises:
            MazeError: If a requested regeneration finds no valid maze.
            OSError: If the output file cannot be written again.
        """
        while True:
            try:
                self._show()
                choice = self._ask()
                if choice == "5":
                    return
                self._apply(choice)
            except (EOFError, KeyboardInterrupt):
                print()
                return

    def _apply(self, choice: str) -> None:
        """Carry out the menu entry the user picked."""
        if choice == "1":
            self._generator = self._build(self._rng.getrandbits(SEED_BITS))
            self._pending = BUILD
        elif choice == "2":
            self._show_path = not self._show_path
            self._pending = SOLVE if self._show_path else None
        elif choice == "3":
            self._palette += 1
        else:
            self._animate = not self._animate

    def _ask(self) -> str:
        """Return the menu entry the user picked.

        Returns:
            One of the accepted choices, asking again until then.

        Raises:
            EOFError: If the input stream is closed.
            KeyboardInterrupt: If the user interrupts the program.
        """
        while True:
            choice = input(PROMPT).strip()
            if choice in CHOICES:
                return choice
            print(INVALID)

    def _build(self, seed: int) -> MazeGenerator:
        """Generate a maze, report a missing pattern and save the file."""
        generator = MazeGenerator(
            width=self._config.width,
            height=self._config.height,
            entry=self._config.entry,
            exit_=self._config.exit_,
            perfect=self._config.perfect,
            seed=seed,
        )
        generator.generate()
        if not generator.pattern_cells:
            print(NO_PATTERN, file=sys.stderr)
        write_maze(
            self._config.output_file,
            generator.to_hex_lines(),
            self._config.entry,
            self._config.exit_,
            generator.solution_directions(),
        )
        return generator

    def _show(self) -> None:
        """Draw the maze, animating what the last choice asked for."""
        pending = self._pending
        self._pending = None
        generator = self._generator
        endpoints = (self._config.entry, self._config.exit_)
        palette = self._palette % len(WALL_PALETTE)
        if pending is None or not self._animating():
            print(self._frame(self._solution(), palette))
        else:
            if pending == BUILD:
                animate_build(
                    self._config.width,
                    self._config.height,
                    generator.pattern_cells,
                    generator.build_steps(),
                    endpoints,
                    palette,
                )
            else:
                print(self._frame([], palette))
            if self._show_path:
                animate_path(
                    generator.cells,
                    generator.pattern_cells,
                    endpoints,
                    generator.solution(),
                    palette,
                )
        print(TITLE)
        for entry in ENTRIES:
            print(entry)

    def _animating(self) -> bool:
        """Tell whether frames may be drawn one over the other."""
        return self._animate and sys.stdout.isatty()

    def _solution(self) -> list[tuple[int, int]]:
        """Return the path to draw, empty while it stays hidden."""
        return self._generator.solution() if self._show_path else []

    def _frame(
        self,
        path: list[tuple[int, int]],
        palette: int,
    ) -> str:
        """Return one still drawing of the current maze."""
        return render(
            self._generator.cells,
            self._generator.pattern_cells,
            self._config.entry,
            self._config.exit_,
            path,
            palette,
        )


def run_session(config: MazeConfig) -> None:
    """Generate a maze and hand it over to the interactive menu.

    Args:
        config: Validated content of the configuration file.

    Raises:
        MazeError: If no maze matching the configuration exists.
        OSError: If the output file cannot be written.
    """
    MazeSession(config).run()
