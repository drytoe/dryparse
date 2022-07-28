"""All errors that can be raised directly by dryparse."""

# TODO write error messages for each exception
from inspect import Parameter
from typing import Sequence

# pylint: disable=missing-class-docstring


class DryParseError(Exception):
    """Base class for all dryparse exceptions."""


class NoMatchingOptionError(DryParseError):
    """
    The option specified on the command line doesn't match any option
    defined for the command being parsed.
    """

    def __init__(self, text: str):
        super().__init__(text)


class OptionRequiresArgumentError(DryParseError):
    """Option requires an argument."""

    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionDoesNotTakeArgumentsError(DryParseError):
    """
    An argument was given to the option, although the option doesn't take any.
    """

    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionArgumentTypeConversionError(DryParseError):
    """
    Option argument cannot be converted to the type defined by the
    corresponding :class:`Option` object.
    """

    def __init__(self, argument: str = None, argtype: type = None):
        self.argument = argument
        self.type = argtype
        super().__init__()


class InvalidArgumentPatternError(DryParseError):
    """
    The given pattern can't be used to construct an :class:`Arguments`
    object.
    """

    def __init__(self):
        super().__init__(
            "The given pattern can't be used to construct an "
            "`Arguments` object"
        )


class PatternAfterFlexiblePatternError(DryParseError):
    """Flexible pattern (e.g. ``(str, ...)``) is not the last pattern."""

    def __init__(self):
        super().__init__(
            "There can be no argument patterns after a (type, ...)-style or "
            "(type, range)-style pattern"
        )


class ArgumentConversionError(DryParseError):
    """
    Command line arguments do not conform to the argument pattern accepted by
    the :class:`Arguments` object.
    """

    def __init__(
        self,
        reason: str = None,
        arguments: Sequence[str] = None,
        index: int = None,
    ):
        msg = "Arguments do not conform to the defined argument pattern"
        if reason:
            msg += "\n  Reason: " + reason
        if arguments:
            msg += (
                f"\n  Argument{'s' if len(arguments) > 1 else ''}: "
                + ", ".join(map(str, arguments))
            )
        if index:
            msg += f"\n  Index: {index}"
        self.arguments = arguments
        self.index = index
        super().__init__(msg)


class VariadicKwargsNotAllowedError(DryParseError):
    """
    Function passed to :any:`dryparse.command` does not support a
    ``**kwargs`` argument.
    """

    def __init__(self):
        super().__init__(
            "**kwargs is not allowed in a decorator-style definition of a "
            "command"
        )


class ValueConversionError(DryParseError):
    """Error while converting CLI argument to python representation."""

    def __init__(self):
        super().__init__(ValueConversionError.__doc__[:-1])


class CallbackDoesNotSupportAllArgumentsError(DryParseError):
    """Callback function does not support arguments passed to it."""

    def __init__(self):
        super().__init__(CallbackDoesNotSupportAllArgumentsError.__doc__[:-1])


class NotEnoughPositionalArgumentsError(DryParseError):
    """
    Not enough positional arguments for the given
    :class:`~dryparse.objects.Arguments` object.
    """

    def __init__(self):
        super().__init__(
            "Not enough positional arguments for the given "
            "`Arguments` object"
        )


class TooManyPositionalArgumentsError(DryParseError):
    """Too many positional arguments."""

    def __init__(self):
        super().__init__(TooManyPositionalArgumentsError.__doc__[:-1])


class ReadOnlyAttributeError(DryParseError):
    """Attribute is read-only."""

    def __init__(self, name: str):
        super().__init__(f"Attribute is read-only: {name}")


class AnnotationMustBeTypeOrSpecialError(DryParseError):
    """Annotation must be a type or a special value."""

    def __init__(self, param: Parameter):
        msg = AnnotationMustBeTypeOrSpecialError.__doc__[:-1]
        if param.name:
            msg += f"  Parameter name: {param.name}"
        if param.annotation:
            msg += f"  Annotation: {param.annotation}"
        super().__init__(msg)


class SelfNotFirstArgumentError(DryParseError):
    """If callback has a self argument, it must be the first."""

    def __init__(self):
        super().__init__(SelfNotFirstArgumentError.__doc__[:-1])
