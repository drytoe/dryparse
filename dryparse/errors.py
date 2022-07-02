"""All errors that can be raised directly by dryparse."""

# TODO write error messages for each exception
from inspect import Parameter
from typing import Sequence

# pylint: disable=missing-class-docstring


class DryParseError(Exception):
    """Base class for all dryparse exceptions."""


class OptionRequiresArgumentError(DryParseError):
    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionDoesNotTakeArgumentsError(DryParseError):
    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionArgumentTypeConversionError(DryParseError):
    def __init__(self, argument: str = None, argtype: type = None):
        self.argument = argument
        self.type = argtype
        super().__init__()


class InvalidArgumentPatternError(DryParseError):
    def __init__(self):
        super().__init__("Invalid argument pattern")


class PatternAfterFlexiblePatternError(DryParseError):
    def __init__(self):
        super().__init__(
            "There can be no argument patterns after a (type, ...)-style or "
            "(type, range)-style pattern"
        )


class ArgumentConversionError(DryParseError):
    def __init__(
        self,
        reason: str = None,
        arguments: Sequence[str] = None,
        index: int = None,
    ):
        msg = "Arguments do not conform to the argument pattern"
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
    def __init__(self):
        super().__init__(
            "**kwargs is not allowed in a decorator-style defintion of a "
            "command"
        )


class ValueConversionError(DryParseError):
    def __init__(self):
        super().__init__(
            "Error while converting CLI string to python representation"
        )


class CallbackDoesNotSupportAllArgumentsError(DryParseError):
    def __init__(self):
        super().__init__(
            "Callback function does not support arguments passed to it"
        )


class NotEnoughPositionalArgumentsError(DryParseError):
    def __init__(self):
        super().__init__("Not enough positional arguments for command")


class TooManyPositionalArgumentsError(DryParseError):
    def __init__(self):
        super().__init__("Too many positional arguments for command")


class ReadOnlyAttributeError(DryParseError):
    def __init__(self, name: str):
        super().__init__(f"Attribute is read-only: {name}")


class AnnotationMustBeTypeOrSpecialError(DryParseError):
    def __init__(self, param: Parameter):
        msg = "Annotation must be a type or a special value if applicable"
        if param.name:
            msg += f"  Parameter name: {param.name}"
        if param.annotation:
            msg += f"  Annotation: {param.annotation}"
        super().__init__(msg)


class SelfNotFirstArgumentError(DryParseError):
    def __init__(self):
        super().__init__(
            "If callback has a self argument, it must be the first"
        )
