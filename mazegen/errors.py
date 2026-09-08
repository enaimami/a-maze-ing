"""Define the exception hierarchy raised by the mazegen package."""


class MazeError(Exception):
    """Serve as the base class of every error raised by mazegen."""


class InvalidParametersError(MazeError):
    """Signal that the generator was built with unusable parameters."""


class MazeGenerationError(MazeError):
    """Signal that no maze matching the requested rules could be built."""
