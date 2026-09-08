"""Generate a maze from a configuration file and display it."""

import sys

from app.config import ConfigError, load_config
from app.menu import run_session
from mazegen import MazeError

USAGE = "Usage: python3 a_maze_ing.py config.txt"


def main(argv: list[str]) -> int:
    """Run the program and return the exit code it must end with.

    Args:
        argv: Command line arguments, the program name included.

    Returns:
        0 when the maze was generated, saved and displayed, 1 otherwise.
    """
    if len(argv) != 2:
        print(USAGE, file=sys.stderr)
        return 1
    try:
        run_session(load_config(argv[1]))
    except (ConfigError, MazeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Error: interrupted by the user", file=sys.stderr)
        return 1
    except EOFError:
        print("Error: unexpected end of input", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error: unexpected failure: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
