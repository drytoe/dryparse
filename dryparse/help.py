import copy
import textwrap
import weakref
from io import StringIO
from typing import Any, Iterable, List, Optional, Union, overload

from dryparse.objects import Command, DryParseType, Group, Meta, Option
from dryparse.util import _NoInit, reassignable_property

AnyGroup = Union[str, Group]
_HelpableObject = Union[Command, Option, Group]
_ConcreteHelp = Union["CommandHelp", "OptionHelp", "GroupHelp"]


class _HelpMetaclass(_NoInit):
    _override_class = None

    @property
    def override_class(self) -> Optional[type]:
        """
        Look at the documentation for this property in any class that has this
        as its metaclass.
        """
        return self._override_class

    @override_class.setter
    def override_class(self, cls: Optional[type]):
        if not issubclass(cls, self.__class__):
            raise TypeError("Argument cls must be a subclass of OptionHelp")
        self._override_class = cls

    # TODO override __call__ so an instance of the configured override_class is
    #  constructed instead of an instance of the given class.


class Help(DryParseType, metaclass=_HelpMetaclass):
    """
    Hierarchical representation of a help message. You can customize every
    individual part or subpart of it, or its entirety.

    Constructing a ``Help`` object will return a specialized object depending
    on the type of the wrapped object ``obj``. This will be one of:
    :class:`OptionHelp`, :class:`CommandHelp`, :class:`GroupHelp`.

    Parameters
    ----------
    obj: Command | Option | Group
        Object for which to construct help.
    """

    _object_to_help_map = weakref.WeakKeyDictionary()

    def __init__(self, obj: _HelpableObject):
        _ = obj  # prevents 'unused' warning
        super().__init__()

    @overload
    def __new__(cls, obj: Command) -> "CommandHelp":
        ...

    @overload
    def __new__(cls, obj: Option) -> "OptionHelp":
        ...

    @overload
    def __new__(cls, obj: Group) -> "GroupHelp":
        ...

    def __new__(cls, obj: _HelpableObject) -> _ConcreteHelp:
        if isinstance(obj, Command):
            class_ = CommandHelp
        elif isinstance(obj, Option):
            class_ = OptionHelp
        elif isinstance(obj, Group):
            class_ = GroupHelp
        else:
            raise TypeError("obj has invalid type")

        if class_.override_class:
            class_ = class_.override_class

        try:
            retval: Any = cls._object_to_help_map[obj]
            return retval
        except KeyError:
            help = cls._object_to_help_map[obj] = super().__new__(class_)
            help.__init__(obj)
            return help

    @reassignable_property
    def text(self):
        raise NotImplementedError

    def __str__(self):
        return self.text

    def _copy_to(self, obj: _HelpableObject):
        """Make ``command``'s help message identical to this one."""
        new = self.__class__._object_to_help_map[obj] = copy.copy(self)
        return new


class CommandHelp(Help, metaclass=_HelpMetaclass):
    """
    Object that represents a command's help message organized as a hierarchy.
    """

    __slots__ = ("command", "_sections")

    def __init__(self, command: Command):
        self.command = command
        self._sections = _CommandHelpSectionList(command)

    def __getattribute__(self, key):
        # The desc attribute is special. No matter how the user overrides it,
        # it should be converted to a CommandDescription
        if key == "desc":
            attr = super().__getattribute__("desc")
            return (
                attr
                if isinstance(attr, CommandDescription)
                else CommandDescription(attr)
            )
        else:
            return super().__getattribute__(key)

    @reassignable_property
    def signature(self):
        """
        Describes the command signature when listed as a subcommand in the help
        message of another command.

        Defaults to the command name.
        """
        return Meta(self.command).name

    @reassignable_property
    def desc(self) -> "CommandDescription":
        """
        Command description.

        You can assign this to be a ``str`` or :class:`CommandDescription`, but
        you will always get a :class:`CommandDescription` when you try to access
        this as an attribute.
        """
        return CommandDescription("")

    @reassignable_property
    def sections(self):
        """Sections of this help message."""
        return self._sections

    @reassignable_property
    def section_separator(self):
        """Separator between sections of this help message."""
        return "\n\n"

    @reassignable_property
    def listing(self):
        """
        Text that appears when this subcommand is listed as a subcommand in the
        help message of another command.
        """
        meta = Meta(self.command)
        return HelpEntry(meta.name, self.desc.brief).text

    @reassignable_property
    def text(self):
        """The entire help text."""
        return self.section_separator.join(
            (sec.text for sec in self.sections if sec.active)
        )

    def _copy_to(self, command: Command):
        new: Any = super()._copy_to(command)
        new: CommandHelp
        new.command = command
        return new


class OptionHelp(Help, metaclass=_HelpMetaclass):
    """
    Attributes
    ----------
    override_class: Optional[Type[OptionHelp]]
        When obtaining a help object using ``Help(option)``, return an instance
        of ``override_class`` instead of :class:`OptionHelp`.
    """

    def __init__(self, option: Option):
        self.option = option

    @reassignable_property
    def desc(self):
        """Option description."""
        return ""

    @reassignable_property
    def argname(self):
        """Name of the argument to this option."""
        return self.option.long.upper()[2:] or self.option.short.upper()[1:]

    @reassignable_property
    def signature(self) -> str:
        """
        Option signature.

        Default value:

        - `-o ARGNAME, --option ARGNAME`, if the option takes an argument
        - `-o ARGNAME`, if the option only has a short text
        - `--option ARGNAME`, if the option only has a long text
        - `--o ARGNAME`, if the option only has a short text
        - `ARGNAME` is omitted if the option takes no argument
        """
        opt = self.option
        long = (
            " ".join(
                filter(
                    None,
                    (
                        opt.long,
                        self.argname if self.option.type != bool else None,
                    ),
                )
            )
            if opt.long
            else None
        )
        short = (
            " ".join(
                filter(
                    None,
                    (
                        opt.short,
                        self.argname if opt.type != bool else None,
                    ),
                )
            )
            if opt.short
            else None
        )
        return ", ".join(filter(None, (short, long)))

    @reassignable_property
    def hint(self):
        """
        Hint for the option that appears in the "usage" section of a command.

        Default value:

        - `[-o ARGNAME]`, if the option has a short text
        - `[--option ARGNAME]`, if the option has no short text
        - `ARGNAME` is omitted if the option does not take an argument
        """
        opt = self.option
        return (
            "["
            + " ".join(
                filter(
                    None,
                    (
                        next(filter(None, (opt.short, opt.long))),
                        self.argname if opt.type != bool else None,
                    ),
                )
            )
            + "]"
        )

    @reassignable_property
    def text(self):
        """The entire help text that overrides all other properties."""
        return HelpEntry(self.signature, self.desc).text

    def _copy_to(self, option: Option):
        new: Any = super()._copy_to(option)
        new: OptionHelp
        new.option = option
        return new


class GroupHelp(Help, metaclass=_HelpMetaclass):
    def __init__(self, group: AnyGroup):
        self.group = group

    @reassignable_property
    def text(self):
        """The entire help text."""
        return ""

    def _copy_to(self, group: Group):
        new: Any = super()._copy_to(group)
        new: GroupHelp
        new.group = group
        return new


class HelpSection(DryParseType):
    def __init__(self, name_or_group: Union[str, Group]):
        if isinstance(name_or_group, str):
            self.name = name_or_group
        elif isinstance(name_or_group, Group):
            self.group = name_or_group
            self.name = lambda _: name_or_group.name
        else:
            raise TypeError("`name_or_group` must be of type str or Group")

    @reassignable_property
    def name(self) -> str:
        """Section name."""
        return ""

    @reassignable_property
    def group(self) -> Optional[Group]:
        return None

    @reassignable_property
    def headline(self):
        """
        Section headline.

        Default value: ``f"{self.name}:"``.
        """
        return f"{self.name}:"

    @reassignable_property
    def content(self) -> str:
        return ""

    @reassignable_property
    def indent(self):
        """Indent for the content of this section."""
        return 2

    @reassignable_property
    def active(self):
        """
        Controls whether the section is displayed.

        Default value: ``True``
        """
        return bool(self.text)

    @reassignable_property
    def text(self):
        """The entire help text."""
        indent = " " * self.indent
        return self.headline + "\n" + textwrap.indent(self.content, indent)

    def __str__(self):
        return self.text

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__}[{repr(self.name)}] at {hex(id(self))}>"


class HelpSectionList(DryParseType, List[HelpSection]):
    """
    A glorified list of help sections.

    Behaves exactly like a normal list, with the addition that you can also
    access individual help sections as attributes, not just by indexing.
    Sections added using regular list functions can only be accessed by index
    (and iterators, etc.), while sections added by attribute assignment can
    also be accessed as attributes. In the latter case, the index is determined
    by the number of sections that existed before the section was added.

    Examples
    --------
    >>> sections = HelpSectionList()
    >>> # Create unnamed section at index 0
    >>> sections.append(HelpSection("Usage"))
    >>> # Create section named usage - index automatically set to be 1
    >>> sections.commands = HelpSection("Commands")
    >>> print(sections[0].text)
    Usage:
    >>> print(sections.usage.text)
    Commands:
    >>> print(sections[1])
    Commands:
    """

    def __init__(self, iterable: Iterable = ()):
        super().__init__(iterable=iterable)

    def __getitem__(self, item: Union[int, str, Group]):
        if isinstance(item, int):
            return super().__getitem__(item)
        elif isinstance(item, str):
            try:
                return next((sec for sec in self if sec.name == item))
            except StopIteration:
                raise KeyError(item)
        elif isinstance(item, Group):
            return next((sec for sec in self if sec.group == item))
        else:
            raise TypeError("`item` must be of type str or int")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        self.append(value)


class HelpEntry(DryParseType):
    """
    Represents an option or subcommand entry in a help message.
    """

    __slots__ = ["signature", "desc"]

    def __init__(self, signature, desc):
        self.signature = signature
        self.desc = desc

    @reassignable_property
    def signature_width(self):
        """
        Width of signature after padding.

        Default: 32 characters.
        """
        return 32

    @reassignable_property
    def padded_signature(self):
        """
        Option signature padded until :attr:`signature_width`.
        """
        return self.signature.ljust(self.signature_width, " ")

    @reassignable_property
    def text(self):
        if self.desc:
            return self.padded_signature + self.desc
        else:
            return self.signature


class CommandDescription:
    """
    Command description that can hold both a long and a brief version.

    Attributes
    ----------
    long: str
        Long description. Used in the help text of the command at hand.
    brief: str
        Brief description. Describes this command when it appears as a
        subcommand in another command's help text. Falls back to ``long``.
    """

    __slots__ = ["long", "brief"]

    def __init__(self, long, brief=None):
        self.long = long
        self.brief = brief or long

    def __str__(self):
        return self.long

    def __repr__(self):
        return repr(self.long)


class _CommandHelpSectionList(HelpSectionList):
    """
    Standard set of help sections for a CLI command.

    Contains a command description, usage, subcommands and options section.
    """

    def __init__(self, command: Command):
        super().__init__()
        self.desc = self.DescSection(command)
        self.usage = self.UsageSection(command)
        self.subcommands = self.CommandsSection(command)
        self.options = self.OptionsSection(command)

    class DescSection(HelpSection):
        __slots__ = ["command"]

        def __init__(self, command: Command):
            super().__init__("description")
            self.command = command
            self.headline = ""

        @reassignable_property
        def text(self):
            return Help(self.command).desc.long

        def __str__(self):
            return self.text

        def __repr__(self):
            return object.__repr__(self)

    class UsageSection(HelpSection):
        __slots__ = ["command"]

        def __init__(self, command: Command):
            super().__init__("usage")
            self.command = command

        @reassignable_property
        def text(self):
            meta = Meta(self.command)
            out = StringIO()
            print(
                f"Usage: {meta.name}",
                " ".join(Help(opt).hint for opt in meta.options),
                file=out,
                end="",
            )
            return out.getvalue()

        def __str__(self):
            return self.text

        def __repr__(self):
            return object.__repr__(self)

    class CommandsSection(HelpSection):
        __slots__ = ["command"]

        def __init__(self, command: Command):
            super().__init__("Commands")
            self.command = command

        @reassignable_property
        def content(self):
            meta = Meta(self.command)
            return "\n".join(
                tuple(Help(cmd).listing for cmd in meta.subcommands)
            )

        @reassignable_property
        def active(self):
            meta = Meta(self.command)
            return bool(meta.subcommands)

    class OptionsSection(HelpSection):
        __slots__ = ["command"]

        def __init__(self, command: Command):
            super().__init__("Options")
            self.command = command

        @reassignable_property
        def content(self):
            meta = Meta(self.command)
            return "\n".join(tuple(Help(opt).text for opt in meta.options))

        @reassignable_property
        def active(self):
            meta = Meta(self.command)
            return bool(meta.options)
