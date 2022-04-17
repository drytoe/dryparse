import inspect
import weakref
from typing import List

from dryparse.util import _NoInit, reassignable_property


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
        Regex pattern that the short version of this option should match
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


class Argument(DryParseType):
    def __init__(self, type: type = str):
        self.type = type
        self.value = None


class Command(DryParseType):
    """
    A CLI command.

    All attributes are either options, subcommands or positional arguments.
    """

    def __init__(self, name, regex=None, desc: str = None):
        meta = Meta(self)
        meta.name = name
        meta.regex = regex or name
        self.help = Option("-h", "--help", desc="print help message and exit")

        if desc is not None:
            from .help import Help
            Help(self).desc = desc

    def __call__(self):
        """
        Execute the command. Unless overridden, this will process special
        options like help and version, and handle subcommands.
        """
        if self.help:
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


class Meta(DryParseType, metaclass=_NoInit):
    """
    Meta wrapper for :class:`Command` that can be used to access special
    attributes of :class:`Command`.
    """
    _command_to_meta_map = weakref.WeakKeyDictionary()

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
            return cls._command_to_meta_map[command]
        except KeyError:
            help = cls._command_to_meta_map[command] = super().__new__(cls)
            help.__init__(command)
            return help

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
            "-v", "--version", desc="print program version and exit"
        )
        Meta(self).version = version

    def __call__(self, *args, version=False, desc=False, **kwargs):
        if version and not help:
            print(f"{Meta(self).regex} version {Meta(self).version}")
        else:
            super().__call__(
                *args, **self.__dict__, version=version, desc=desc, **kwargs
            )
