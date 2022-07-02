"""Module containing special option types."""
from dryparse.objects import DryParseType

__all__ = ("OptionType", "Counter", "Bool")


class OptionType(DryParseType):
    """
    Base class for all option value types.

    You can create custom types by subclassing this class.

    Attributes
    ----------
    takes_argument: bool
        Whether the option value is specified as an argument to the option or
        is derived from the presence of the option itself.
    value: Any
        The option argument converted to an arbitrary type.
    """

    takes_argument = True

    def __init__(self, value: str):
        self.value = value


class Counter(OptionType):
    """A counter that increments each time an option is specified."""

    takes_argument = False

    def __new__(cls, value: str):
        # pylint: disable=super-init-not-called
        pass  # TODO


class Bool(OptionType):
    """
    A bool type that understands ``"true"``, ``"True"``, ``"false"``,
    ``"False"`` and empty string.
    """

    def __new__(cls, value: str):
        if value in ("true", "True", "yes"):
            return True
        if value in ("false", "False", "no"):
            return False

        raise ValueError(value)
