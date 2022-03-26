import inspect
from types import SimpleNamespace
from typing import List


class DryParseType:
    """Exists so all dryparse objects can share the same parent."""

    pass


class Option(DryParseType):
    """
    Parameters
    ----------
    short: str
        Regex pattern that the short version of this option should match
        against. Usually this is a hyphen followed by a single letter.
    long: str
        Regex pattern that the short version of this option should match
        against. Usually this is two hyphens followed by multiple letters.
    """

    def __init__(
        self,
        short: str = "",
        long: str = "",
        hint: str = None,
        signature: str = None,
        metavar: str = None,
        default=None,
        type: type = bool,
        help="",
    ):
        if not (short or long):
            raise ValueError()
        self.short = short
        self.long = long
        self.help = help
        self.metavar = metavar
        self._hint = hint
        self._signature = signature
        self.type = type
        if default:
            self.value = default
        else:
            self.value = None

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
        what formats are acceptable for the option. Unless custom `hint` or
        `signature` handlers are given, the positional argument names are used
        to generate the help message.

        The build function can be assigned by `option.build = <function>`.

        Parameters
        ----------
        option
            The exact way the option was specified. This is useful when the
            option text is specified as a regex, or when you want to know if the
            option was specified using its short or long format.

        Examples
        --------
        Assume that the long version of the option is `--option`.

        1. If the signature is `build(self, **kwargs)`, the option is a
           ``bool`` option and can be specified as `--option`.
        2. If the signature is `build(self, arg, **kwargs)`, the option can be
           specified as `--option ARG`
        """
        self.value = True

    @property
    def hint(self):
        if self._hint:
            return self._hint
        else:
            return (
                "["
                + " ".join(
                    filter(
                        None,
                        (
                            next(filter(None, (self.short, self.long)), None),
                            (self.metavar or self.long.upper()[2:])
                            if self.type != bool
                            else None,
                        ),
                    )
                )
                + "]"
            )

    @property
    def signature(self):
        if self._signature:
            return self._signature

        long = " ".join(
            filter(
                None,
                (
                    self.long,
                    (self.metavar or self.long.upper()[2:])
                    if self.type != bool
                    else None,
                ),
            )
        ) if self.long else None
        short = " ".join(
            filter(
                None,
                (
                    self.short,
                    self.metavar or self.long.upper()[2:]
                    if self.type != bool
                    else None,
                ),
            )
        ) if self.short else None
        return ", ".join(filter(None, (short, long)))


class Argument(DryParseType):
    def __init__(self, type: type = str):
        self.type = type
        self.value = None


class Command(DryParseType):
    """
    A CLI command.
    """

    def __init__(self, name, regex=None, desc=""):
        meta = Meta(self)
        meta.name = name
        meta.regex = regex or name
        meta.desc = desc
        self.help = Option("-h", "--help", help="print help message and exit")

    def __call__(self):
        """
        Execute the command. Unless overridden, this will process special
        options like help and version, and handle subcommands.
        """
        if self.help:
            from .util import get_help

            print(get_help(self))
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
        elif isinstance(value, Argument):
            super().__setattr__(name, value)
            Meta(self).arguments.append(value)
        elif (
            isinstance(value, list)
            and value
            and all([isinstance(item, Argument) for item in value])
        ):
            # ``value`` is a list of Arguments
            super().__setattr__(name, value)
            Meta(self).arguments += value
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
        elif isinstance(value, Argument):
            Meta(self).arguments.remove(value)
        elif (
            isinstance(value, list)
            and value
            and all([isinstance(item, Argument) for item in value])
        ):
            # ``value`` is a list of Arguments
            Meta(self).arguments[:] = [
                arg for arg in Meta(self).arguments if arg not in value
            ]
        super().__delattr__(name)


class __NoInit(type):
    def __call__(cls, *args, **kwargs):
        return cls.__new__(cls, *args, **kwargs)


class Meta(DryParseType, metaclass=__NoInit):
    """
    Meta wrapper for :class:`Command` that can be used to access special
    attributes of :class:`Command`.
    """

    __slots__ = [
        "options",
        "subcommands",
        "arguments",
        "name",
        "regex",
        "desc",
    ]

    def __init__(self, command: Command):
        self.options: List[Option] = []
        self.subcommands: List[Command] = []
        self.arguments: List[Argument] = []
        self.name = ""
        self.regex = ""
        self.desc = ""
        _ = command  # prevents some warnings

    def __new__(cls, command: Command):
        try:
            return command._dryparse_command_meta
        except AttributeError:
            meta = command._dryparse_command_meta = super().__new__(cls)
            meta.__init__(command)
            return meta

    def __setattr__(self, key, value):
        if key == "call":
            super().__setattr__(key, value.__get__)
        super().__setattr__(key, value)

    def call(self, *args, **kwargs):
        pass


class RootCommand(Command):
    """Command that corresponds to the program itself."""

    def __init__(self, name, regex="", desc="", version=""):
        super().__init__(name, regex=regex, desc=desc)
        self.version = Option(
            "-v", "--version", help="print program version and exit"
        )
        Meta(self).version = version

    def __call__(self, *args, version=False, help=False, **kwargs):
        if version and not help:
            print(f"{Meta(self).regex} version {Meta(self).version}")
        else:
            super().__call__(*args, version=version, help=help, **kwargs)
