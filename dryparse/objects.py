"""Object model of a command line program."""
import copy
import inspect
from typing import Any, Callable, List, NoReturn, Sequence, Tuple, Union
from weakref import WeakKeyDictionary

from dryparse.errors import (
    ArgumentConversionError,
    InvalidArgumentPatternError,
    PatternAfterFlexiblePatternError,
)
from dryparse.util import _NoInit

_EllipsisType = type(Ellipsis)


class DryParseType:
    """Exists so all dryparse objects can share the same parent."""


class Group(DryParseType):
    """A group of commands or options."""

    def __init__(self, name: str):
        self.name = name
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .help import GroupHelp

        self.help = GroupHelp(self)


class Option(DryParseType):
    """
    Parameters
    ----------
    short: str
        Regex pattern that the short version of this option should match
        against. Usually this is a hyphen followed by a single letter
        (e.g. `-s`).
    long: str
        Regex pattern that the long version of this option should match
        against. Usually this is two hyphens followed by multiple letters.
        (e.g. `--long`)
    Attributes
    ----------
    help: OptionHelp
        Customizable help object.
    """

    def __init__(
        self,
        short: str = "",
        long: str = "",
        argname: str = None,
        default=None,
        argtype: type = bool,
        desc: str = None,
    ):
        if not (short or long):
            raise ValueError("An option must have short or long text")
        self.short = short
        self.long = long
        self.type = argtype
        if default:
            self.value = default
        else:
            self.value = None

        # pylint: disable=import-outside-toplevel,cyclic-import
        from .help import OptionHelp

        self.help = OptionHelp(self)
        if argname is not None:
            self.help.argname = argname
        if desc is not None:
            self.help.desc = desc

    def __setattr__(self, key, value):
        if key == "build":
            if not inspect.isfunction(value):
                raise TypeError("'build' must be a function.")
            # Bind the function `value` to self.build
            super().__setattr__(key, value.__get__(self, type(self)))
        else:
            super().__setattr__(key, value)

    def build(self, option: str = None):
        """
        Each time this option is specified on the command line, this method is
        called. The positional arguments in the function signature determine
        what formats are acceptable for the option.

        The build function can be assigned by `option.build = <function>`.

        Parameters
        ----------
        option
            The exact way the option was specified. This is useful when the
            option text is specified as a regex, or when you want to know if
            the option was specified using its short or long format.

        Examples
        --------
        Assume that the long version of the option is `--option`.

        1. If the signature is `build(self, **kwargs)`, the option is a
           ``bool`` option and can be specified as `--option`.
        2. If the signature is `build(self, arg, **kwargs)`, the option can be
           specified as `--option ARG`
        """
        _ = option  # TODO
        self.value = True


class Arguments(DryParseType):
    """
    Specification for positional arguments of a command.

    Positional arguments are specified on the command line as regular strings,
    but usually we want to restrict the number of allowed arguments, their data
    types, add custom validation, etc. An instance of :class:`Arguments` holds
    a pattern of acceptable argument types. The arguments are converted
    (and effectively validated) using :meth:`convert`.

    Attributes
    ----------
    pattern
        Determines the number of arguments and their types. Each item of this
        list represents an argument or multiple arguments of a given type. The
        order of arguments is important.

        There are two acceptable formats for each entry:

        - *type*: Accepts a single argument of the given type.
        - (*type*, *number*): Accepts *number* arguments of type *type*.

        Note that *number* can be an ``int``, ``...`` (ellipsis) or ``range``.
        An ``int`` specifies a fixed number of required arguments. Ellipsis is
        a special value meaning *zero or more arguments*. A range specifies a
        range of acceptable argument numbers.

    Notes
    -----
    - ``(type, ...)``- and ``(type, range)``- style patterns cannot be followed
      by further patterns. Instead, you should implement a custom converter
      function.
    - For boolean types, you might want to use :class:`~dryparse.types.Bool`
      instead of ``bool``, because of potentially undesired behaviors like
      ``bool("false") == True``, etc.

    Examples
    --------

    Here's quite an exhaustive list of example use cases:

    >>> # Single argument of type int
    >>> Arguments(int)
    >>> # Two arguments of type bool
    >>> Arguments((bool, 2))
    >>> # Single int and two bools
    >>> Arguments(int, (bool, 2))
    >>> # Zero or more strings
    >>> Arguments((str, ...))
    >>> # One or more strings
    >>> Arguments(str, (str, ...))
    >>> # Between 2 and 4 strings
    >>> Arguments((str, range(2, 4)))
    >>> # One int and zero or more strings
    >>> Arguments(int, (str, ...))
    >>> # ERROR: there can be no patterns after a (type, ...)-style pattern
    >>> Arguments(int, (int, ...), str)
    >>> # ERROR: there can be no patterns after a (type, range)-style pattern
    >>> Arguments(int, (int, range(1, 2)), str)
    """

    __slots__ = ("types", "value", "defaults")

    _NumberOfArgs = Union[int, _EllipsisType, range]
    _PatternItem = Union[type, Tuple[type, _NumberOfArgs]]

    def __init__(
        self,
        *pattern: _PatternItem,
    ):
        if not pattern:
            self.pattern = [(str, ...)]
            return
        # NOTE: when referring to a flexible pattern, we mean either a
        # (type, ...)-style or a (type, range)-style pattern
        flexible_pattern_found = False
        for item in pattern:
            if flexible_pattern_found:
                raise PatternAfterFlexiblePatternError
            if isinstance(item, tuple):
                # pylint: disable=no-else-raise
                if len(item) != 2:
                    raise InvalidArgumentPatternError
                elif isinstance(item[1], (_EllipsisType, range)):
                    flexible_pattern_found = True
                elif not isinstance(item[0], type) or (
                    not isinstance(item[1], (_EllipsisType, range))
                    # Hint: a bool is also an int, but we don't allow it
                    and not (
                        not isinstance(item[1], bool)
                        and isinstance(item[1], int)
                        and item[1] > 0
                    )
                ):
                    raise InvalidArgumentPatternError
            elif not isinstance(item, type):
                raise InvalidArgumentPatternError
        self.pattern = pattern

    def convert(self, args: Sequence[str]) -> Union[List[Any], Any]:
        """
        Convert (and consequently validate) a list of ``args`` that were
        possibly specified on the command line to a list of arguments
        conforming to :attr:`pattern`.

        If the conversion of any of the arguments throws an exception, the
        conversion (and validation) will fail. (TODO exception)
        """
        # pylint: disable=too-many-branches

        converted_args = []
        flexible_pattern: Union[Tuple[_EllipsisType, range], None] = None
        arg_index = 0
        pattern: Arguments._PatternItem

        def msg_expected_more_input_args(pattern_: Arguments._PatternItem):
            return (
                f"Pattern {self._pattern_item_to_str(pattern_)} "
                f"expected more input arguments"
            )

        def raise_type_conversion_error(
            original_err: Exception,
            pattern_: Arguments._PatternItem,
            args_: Sequence[str],
        ) -> NoReturn:
            raise ArgumentConversionError(
                f"Argument could not be converted to specified type: "
                f"{self._pattern_item_to_str(pattern_)}",
                arguments=args_,
                index=arg_index,
            ) from original_err

        for pattern in self.pattern:
            # If there is a flexible pattern, it can only be at the end.
            # This pattern will be handled separately.
            if isinstance(pattern, tuple) and isinstance(
                pattern[1], (_EllipsisType, range)
            ):
                flexible_pattern = pattern
                break

            if isinstance(pattern, type):
                pattern: type
                try:
                    arg = args[arg_index]
                except IndexError:
                    # pylint: disable=raise-missing-from
                    raise ArgumentConversionError(
                        msg_expected_more_input_args(pattern)
                    )
                converted = None
                try:
                    converted = pattern(arg)
                except Exception as e:
                    raise_type_conversion_error(e, pattern, (arg,))
                converted_args.append(converted)
                arg_index += 1
            elif isinstance(pattern, tuple):
                type_: type = pattern[0]
                number: int = pattern[1]
                if len(args) - arg_index < number:
                    raise ArgumentConversionError(
                        msg_expected_more_input_args(pattern),
                    )
                converted_args += map(
                    type_, args[arg_index : arg_index + number]
                )
                arg_index += number

        if isinstance(flexible_pattern, tuple):
            pattern = flexible_pattern
            number: Union[_EllipsisType, range] = pattern[1]
            if isinstance(number, _EllipsisType):
                try:
                    converted_args += map(pattern[0], args[arg_index:])
                except Exception as e:
                    raise_type_conversion_error(e, pattern, args[arg_index:])
            elif isinstance(number, range):
                remaining_length = len(args) - arg_index
                if number.start <= remaining_length <= number.stop:
                    converted_args += map(pattern[0], args[arg_index:])
                else:
                    raise ArgumentConversionError(
                        f"Wrong number of input args for pattern: "
                        f"{self._pattern_item_to_str(self.pattern[-1])}"
                    )
        elif len(args) - arg_index > 0:
            raise ArgumentConversionError("Too many input arguments")

        if len(self.pattern) == 1 and (
            isinstance(self.pattern[0], type)
            or isinstance(self.pattern[0], tuple)
            and self.pattern[0][1] == 1
        ):
            return converted_args[0]
        return converted_args

    def assign(self, args: List[str]):
        """
        Assign a set of arguments specified on the command line to be held by
        this instance.

        The arguments are converted and validated using :meth:`convert` to
        conform to :attr:`pattern`.
        """
        # pylint: disable=attribute-defined-outside-init
        self._args = self.convert(args)

    def __iter__(self):
        return iter(self._args)

    @staticmethod
    def _pattern_item_to_str(pattern_item: _PatternItem):
        # pylint: disable=no-else-return
        if isinstance(pattern_item, type):
            return pattern_item.__name__
        elif isinstance(pattern_item, tuple):
            return f"({', '.join(str(pattern_item))})"
        else:
            raise TypeError(pattern_item)


class Command(DryParseType):
    """
    A CLI command.

    You can assign arbitrary attributes dynamically. Only attributes of types
    :class:`Option`, :class:`Command`, :class:`Group` and others from
    :mod:`dryparse.objects` have special meaning to the parser.

    Examples
    --------
    >>> docker = Command("docker")
    >>> docker.context = Option("-c", "--context")
    >>> docker.run = Command("run", desc="Run a command in a new container")
    """

    def __init__(self, name, regex=None, desc: str = None):
        meta = Meta(self)
        meta.name = name
        meta.regex = regex or name
        self.help = Option("-h", "--help", desc="print help message and exit")

        if desc is not None:
            meta.help.desc = desc

    def __call__(self, *args, help=None, **kwargs):
        """
        Execute the command. Unless overridden, this will process special
        options like help and version, and handle subcommands.
        """
        # pylint: disable=redefined-builtin
        if help or (help is None and hasattr(self, "help") and self.help):
            print(Meta(self).help.text)
        else:
            Meta(self).call(self, *args, help=help, **kwargs)

    def __setattr__(self, name, value):
        if isinstance(value, Option):
            super().__setattr__(name, value)
            Meta(self).options.append(value)
        elif isinstance(value, Command):
            super().__setattr__(name, value)
            Meta(self).subcommands.append(value)
        else:
            try:
                attr = super().__getattribute__(name)
            except AttributeError:
                attr = None
            if isinstance(attr, Option):
                option: Option = attr
                option.value = value
            else:
                super().__setattr__(name, value)

    def __copy__(self):
        return copy.deepcopy(self)

    def __deepcopy__(self, memo=None):
        new = copy.deepcopy(super(), memo)
        new.__class__ = self.__class__
        Meta(self)._copy_to(Meta(new), memo)
        return new

    def __delattr__(self, name):
        value = super().__getattribute__(name)
        if isinstance(value, Option):
            Meta(self).options.remove(value)
        elif isinstance(value, Command):
            Meta(self).subcommands.remove(value)
        super().__delattr__(name)


class ParsedCommand(Command):
    """
    Wrapper around :class:`Command` that provides access to option values as if
    they were regular attributes.

    Examples
    --------
    >>> # Initialize a simple command with an option
    >>> cmd = Command("test")
    >>> cmd.option = Option("--option", default="DEFAULT")
    >>> # Convert Command into a ParsedCommand
    >>> parsed_cmd = ParsedCommand(cmd)
    >>> print(parsed_cmd.option)
    DEFAULT
    >>> # Assignment works like with a regular command
    >>> parsed_cmd.option = "NON_DEFAULT"
    >>> print(parsed_cmd)
    NON_DEFAULT
    """

    def __init__(self, command: Command):
        # pylint: disable=unused-argument
        # pylint: disable=super-init-not-called
        pass

    def __new__(cls, command: Command):
        parsed_cmd = copy.deepcopy(command)
        # Matches any of the `Command` subclasses defined in this module
        if command.__module__ == cls.__module__:
            parsed_cmd.__class__ = ParsedCommand
        else:
            # All bases that are subclasses of `Command` and were defined in
            # this module (not by the dryparse library user) are replaced by
            # `ParsedCommand`.
            parsed_cmd.__bases__ = type(parsed_cmd.__bases__)(
                (
                    base
                    if not isinstance(base, Command)
                    and base.__module__ == cls.__module__
                    else ParsedCommand
                )
                for base in parsed_cmd.__bases__
            )
        return parsed_cmd

    def __getattribute__(self, name):
        """
        If the attribute is an option, return its value. Otherwise, it has the
        default behavior.
        """

        attr = super().__getattribute__(name)
        if isinstance(attr, Option):
            return attr.value
        return attr


class RootCommand(Command):
    """
    Command that corresponds to the program itself.

    Parameters
    ----------
    version: str
        Version of the program that is printed when the `--version` option is
        given.
    """

    def __init__(self, name, regex=None, desc="", version="0.0.0"):
        super().__init__(name, regex=regex, desc=desc)
        self.version = Option(
            "-v", "--version", desc="print program version and exit"
        )
        Meta(self).version = version

    def __call__(self, *args, version=False, **kwargs):
        if hasattr(self, "version") and version and "help" not in kwargs:
            print(f"{Meta(self).regex} version {Meta(self).version}")
        else:
            super().__call__(*args, version=version, **kwargs)


class Meta(DryParseType, metaclass=_NoInit):
    """
    Meta wrapper for :class:`Command` that can be used to access special
    attributes of :class:`Command`.
    """

    _command_to_meta_map = WeakKeyDictionary()

    def __init__(self, command: Command):
        self.options: List[Option] = []
        self.command = command
        self.subcommands: List[Command] = []
        self.arguments = None
        self.name = ""
        self.regex = ""
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .help import CommandHelp

        self.help = CommandHelp(command)

    def __new__(cls, command: Command):
        try:
            return cls._command_to_meta_map[command]
        except KeyError:
            meta = cls._command_to_meta_map[command] = super().__new__(cls)
            meta.__init__(command)
            return meta

    def call(self, *args, **kwargs):  # pylint: disable=method-hidden
        """Callback function for when this command is invoked."""

    def set_callback(self, func: Callable[[Command], Any]):
        """
        Set the callback function to be called when this command is
        invoked.
        """
        self.call = func

    def _copy_to(self, destination: "Meta", memo=None):
        """Perform a deep copy from ``self`` to ``destination``."""
        destination.options = copy.deepcopy(self.options, memo=memo)
        destination.subcommands = copy.deepcopy(self.subcommands, memo=memo)
        destination.arguments = self.arguments
        destination.name = self.name
        destination.regex = self.regex
        destination.help = copy.deepcopy(self.help, memo=memo)
        destination.call = self.call
