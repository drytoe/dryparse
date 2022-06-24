"""Object model of a command line program."""

import inspect
from collections.abc import Sequence
from types import EllipsisType
from typing import Any, Callable, List, Tuple, Union
from weakref import WeakKeyDictionary

from dryparse.util import _NoInit


class DryParseType:
    """Exists so all dryparse objects can share the same parent."""


class Group(DryParseType):
    """A group of commands or options."""

    def __init__(self, name: str):
        self.name = name


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
    """

    def __init__(
        self,
        short: str = "",
        long: str = "",
        argname: str = None,
        default=None,
        type: type = bool,
        desc: str = None,
    ):
        if not (short or long):
            raise ValueError("An option must have short or long text")
        self.short = short
        self.long = long
        self.type = type
        if default:
            self.value = default
        else:
            self.value = None
        if not (argname is None and desc is None):
            from .help import Help

            if argname is not None:
                Help(self).argname = argname
            if desc is not None:
                Help(self).desc = desc

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
        self.value = True


class Arguments(DryParseType):
    """
    Specification for positional arguments of a command.

    Positional arguments are specified on the command line as strings. There
    must be a way to verify if the correct number of arguments was given, and
    a way to convert each one to a useful python type. An instance of :class:`Arguments` holds a
    pattern of acceptable arguments. The arguments are converted
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

    Examples
    --------

    Here's quite an exhaustive list of example use cases:

    >>> # Single argument of type int
    >>> Arguments([int])
    >>> # Two arguments of type bool
    >>> Arguments([(bool, 2)])
    >>> # Single int and two bools
    >>> Arguments([int, (bool, 2)])
    >>> # Zero or more strings
    >>> Arguments([(str, ...)])
    >>> # One or more strings
    >>> Arguments([str, (str, ...)])
    >>> # Between 2 and 4 strings
    >>> Arguments([(str, range(2, 4))])
    >>> # One int and zero or more strings
    >>> Arguments([int, (str, ...)])
    >>> # Zero or more ints, and a string at the end
    >>> Arguments([(int, ...), str])
    >>> # 1 or more ints, 2-3 strings
    >>> Arguments([int, (int, ...), (str, range(2, 3))])
    """

    _NumberOfArgs = Union[int, EllipsisType, range]
    _PatternItem = Union[type, Tuple[type, _NumberOfArgs]]

    __slots__ = ["types", "value", "defaults"]

    def __init__(
        self,
        pattern: Sequence[_PatternItem],
    ):
        self.pattern = pattern

    def convert(self, args: List[str]):
        """
        Convert (and consequently validate) a list of ``args`` specified on the
        command line to a list of arguments conforming to :attr:`pattern`.

        If the conversion of any of the arguments throws an exception, the
        conversion (and validation) will fail. (TODO exception)
        """
        # args with type conversions from self.pattern applied
        modified_args = []
        pattern_index = 0
        arg_index = 0
        args_per_pattern_item = [[]] * len(self.pattern)
        assigned_pattern_item_for_arg: List[Any] = [None] * len(args)
        while True:
            pattern_item = self.pattern[pattern_index]
            # Minimum and maximum number of arguments that can be associated
            # with pattern_item
            min_num_of_args = self._min_num_of_args(pattern_item)
            max_num_of_args = self._max_num_of_args(pattern_item)

            if min_num_of_args > len(args) - arg_index:
                # TODO concrete exception subclass
                raise Exception(
                    f"Not enough arguments to satisfy pattern {pattern_item}"
                )
            # To each pattern_item assigns a range of arguments that conform
            # to that pattern item
            args_per_pattern_item[pattern_index] += range(
                arg_index, arg_index + max_num_of_args
            )
            # Assigns the necessary number of args to pattern_items in order
            # for the pattern to be satisfied
            assigned_pattern_item_for_arg[
                arg_index : arg_index + min_num_of_args
            ] = pattern_index

            pattern_index += 1
            if pattern_index >= len(self.pattern):
                break
            arg_index += min_num_of_args

        for i, arg in enumerate(args):
            assigned_pattern_item_index = assigned_pattern_item_for_arg[i]
            if assigned_pattern_item_for_arg[i] is not None:
                modified_args[i] = self.pattern[assigned_pattern_item_index][0]

    def assign(self, args: List[str]):
        """
        Assign a set of arguments specified on the command line to be held by
        this instance.

        The arguments are converted and validated using :meth:`convert` to
        conform to :attr:`pattern`.
        """
        self._args = self.convert(args)

    def __iter__(self):
        return iter(self._args)

    @staticmethod
    def _min_num_of_args(pattern_item: _PatternItem):
        if isinstance(pattern_item, type):
            return 1
        else:
            number = pattern_item[1]
            if isinstance(number, int):
                return number
            if isinstance(number, EllipsisType):
                return 0
            if isinstance(number, range):
                return number.start

    @staticmethod
    def _max_num_of_args(pattern_item: _PatternItem):
        if isinstance(pattern_item, type):
            return 1
        else:
            number = pattern_item[1]
            if isinstance(number, int):
                return number
            if isinstance(number, EllipsisType):
                return 999999999
            if isinstance(number, range):
                return number.stop

    @staticmethod
    def _pattern_item_to_str(pattern_item: _PatternItem):
        if isinstance(pattern_item, type):
            return pattern_item.__name__
        if isinstance(pattern_item, tuple):
            return f"({', '.join(pattern_item)})"

    class _PatternItemWrapper:
        """
        TODO delete
        An instance of this class wraps a single CLI argument, using its index
        when creating a hash of itself. This is used so that equal arguments.
        """

        def __init__(self, pattern_item: "Arguments._PatternItem", index: int):
            pass

        def __hash__(self):
            pass


class Command(DryParseType):
    """
    A CLI command.

    You can assign arbitrary attributes dynamically. Only attributes of types
    :class:`Option`, :class:`Command`, :class:`Group` and others from
    :mod:`dryparse.objects` have special meaning. Note that getting an
    attribute of type :class:`Option` will return its value, not the option
    itself.

    Examples
    --------
    >>> cmd = Command("docker")
    >>> cmd.context = Option("-c", "--context")
    >>> print(cmd.context)
    False
    """

    def __init__(self, name, regex=None, desc: str = None):
        meta = Meta(self)
        meta.name = name
        meta.regex = regex or name
        self.help = Option("-h", "--help", desc="print help message and exit")

        if desc is not None:
            from .help import Help

            Help(self).desc = desc

    def __call__(self, *args, help=None, **kwargs):
        """
        Execute the command. Unless overridden, this will process special
        options like help and version, and handle subcommands.
        """
        if help or (help is None and hasattr(self, "help") and self.help):
            from .help import Help

            print(Help(self).text)
        else:
            Meta(self).call()

    def __getattribute__(self, name):
        """
        If the attribute is an option, return its value. Otherwise has the
        default behavior.
        """
        attr = super().__getattribute__(name)
        if isinstance(attr, Option):
            return attr.value
        return attr

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
            if isinstance(option := attr, Option):
                option: Option
                option.value = value
            else:
                super().__setattr__(name, value)

    def __delattr__(self, name):
        value = super().__getattribute__(name)
        if isinstance(value, Option):
            Meta(self).options.remove(value)
        elif isinstance(value, Command):
            Meta(self).subcommands.remove(value)
        super().__delattr__(name)


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

    Attributes
    ----------
    called: bool
        Indicates whether this command was called.
    """

    _command_to_meta_map: WeakKeyDictionary[
        Command, "Meta"
    ] = WeakKeyDictionary()

    def __init__(self, command: Command):
        self.options: List[Option] = []
        self.command = command
        self.subcommands: List[Command] = []
        self.arguments = None
        self.name = ""
        self.regex = ""
        self.called = False
        _ = command  # prevents some warnings

    def __new__(cls, command: Command):
        try:
            return cls._command_to_meta_map[command]
        except KeyError:
            help = cls._command_to_meta_map[command] = super().__new__(cls)
            help.__init__(command)
            return help

    def call(self, *args, **kwargs):
        pass

    def callback(self, func: Callable):
        self.call = func
