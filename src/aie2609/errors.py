"""Project-specific exceptions."""


class DataValidationError(ValueError):
    """Raised when an input file violates its documented contract."""


class ClassificationError(ValueError):
    """A model response failed validation; messages never contain raw response text."""


class RunError(RuntimeError):
    """A classification run cannot safely continue."""
