"""Module containing special option types."""
from dryparse.objects import DryParseType


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

    def __init__(self):
        pass  # TODO
