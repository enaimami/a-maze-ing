"""Write a generated maze to its output file."""

from mazegen.grid import Cell


def write_maze(
    path: str,
    hex_lines: list[str],
    entry: Cell,
    exit_: Cell,
    directions: str,
) -> None:
    """Write a maze, its endpoints and its solution to a file.

    The rows of hexadecimal digits come first, then an empty line, then
    the entry, the exit and the shortest path, each on its own line.

    Args:
        path: Location of the file to write.
        hex_lines: One lowercase hexadecimal string per row of cells.
        entry: Cell the player enters from.
        exit_: Cell the player leaves from.
        directions: Shortest path as N, E, S and W letters.

    Raises:
        OSError: If the file cannot be created or written.
    """
    lines = list(hex_lines)
    lines.append("")
    lines.append(f"{entry[0]},{entry[1]}")
    lines.append(f"{exit_[0]},{exit_[1]}")
    lines.append(directions)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            for line in lines:
                handle.write(f"{line}\n")
    except OSError as error:
        raise OSError(
            f"cannot write '{path}': {error.strerror}"
        ) from error
