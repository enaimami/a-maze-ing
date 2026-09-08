"""Read and validate the configuration file of the program."""

import re
from dataclasses import dataclass

from mazegen.grid import Cell

REQUIRED_KEYS = (
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
)
OPTIONAL_KEYS = ("SEED",)
BOOLEANS = {"true": True, "false": False}
INTEGER = re.compile(r"[+-]?[0-9]+\Z")
COMMENT = "#"
SEPARATOR = "="
MIN_SIDE = 2


class ConfigError(Exception):
    """Signal that the configuration file cannot be used."""


@dataclass(frozen=True)
class MazeConfig:
    """Hold the validated content of a configuration file."""

    width: int
    height: int
    entry: Cell
    exit_: Cell
    output_file: str
    perfect: bool
    seed: int | None


def load_config(path: str) -> MazeConfig:
    """Return the configuration stored in a file.

    Args:
        path: Location of the configuration file.

    Returns:
        The validated configuration of the maze to generate.

    Raises:
        ConfigError: If the file cannot be read, if a line is malformed,
            if a key is missing, unknown or repeated, or if a value is
            outside of its allowed range.
    """
    values = _read_pairs(path)
    for key in REQUIRED_KEYS:
        if key not in values:
            raise ConfigError(f"missing key '{key}' in '{path}'")
    width = _read_side("WIDTH", values["WIDTH"])
    height = _read_side("HEIGHT", values["HEIGHT"])
    entry = _read_cell("ENTRY", values["ENTRY"], width, height)
    exit_ = _read_cell("EXIT", values["EXIT"], width, height)
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells")
    if not values["OUTPUT_FILE"]:
        raise ConfigError("OUTPUT_FILE must not be empty")
    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit_=exit_,
        output_file=values["OUTPUT_FILE"],
        perfect=_read_bool("PERFECT", values["PERFECT"]),
        seed=(
            _read_int("SEED", values["SEED"])
            if "SEED" in values
            else None
        ),
    )


def _read_pairs(path: str) -> dict[str, str]:
    """Return the raw key and value pairs written in a file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as error:
        raise ConfigError(
            f"cannot read '{path}': {error.strerror}"
        ) from error
    except UnicodeDecodeError as error:
        raise ConfigError(f"'{path}' is not valid UTF-8 text") from error
    values: dict[str, str] = {}
    for number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text or text.startswith(COMMENT):
            continue
        if SEPARATOR not in text:
            raise ConfigError(
                f"line {number}: missing '{SEPARATOR}' separator"
            )
        key, _, value = text.partition(SEPARATOR)
        key = key.strip()
        if key not in REQUIRED_KEYS and key not in OPTIONAL_KEYS:
            raise ConfigError(f"line {number}: unknown key '{key}'")
        if key in values:
            raise ConfigError(f"line {number}: duplicate key '{key}'")
        values[key] = value.strip()
    return values


def _read_int(key: str, raw: str) -> int:
    """Return the integer written in a value, or refuse it."""
    if not INTEGER.match(raw):
        raise ConfigError(f"{key} must be an integer, got '{raw}'")
    return int(raw)


def _read_side(key: str, raw: str) -> int:
    """Return the number of cells written in a value, or refuse it."""
    side = _read_int(key, raw)
    if side < MIN_SIDE:
        raise ConfigError(f"{key} must be at least {MIN_SIDE}, got {side}")
    return side


def _read_cell(key: str, raw: str, width: int, height: int) -> Cell:
    """Return the in-bounds cell written in a value, or refuse it."""
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be written 'x,y', got '{raw}'")
    x = _read_int(f"{key} abscissa", parts[0].strip())
    y = _read_int(f"{key} ordinate", parts[1].strip())
    if not 0 <= x < width or not 0 <= y < height:
        raise ConfigError(
            f"{key} ({x},{y}) lies outside a {width}x{height} maze"
        )
    return (x, y)


def _read_bool(key: str, raw: str) -> bool:
    """Return the boolean written in a value, or refuse it."""
    if raw.lower() not in BOOLEANS:
        raise ConfigError(f"{key} must be True or False, got '{raw}'")
    return BOOLEANS[raw.lower()]
