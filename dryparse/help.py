"""Help module for dryparse objects."""

import copy
import textwrap
from io import StringIO
from typing import List, Optional, Union

from dryparse.objects import Command, DryParseType, Group, Meta, Option
from dryparse.util import reassignable_property

AnyGroup = Union[str, Group]
_HelpableObject = Union[Command, Option, Group]
_ConcreteHelp = Union["CommandHelp", "OptionHelp", "GroupHelp"]


class _HelpMetaclass(type):
    _override_class = None

    @property
    def override_class(cls) -> Optional[type]:
        """
        Look at the documentation for this property in any class that has this
        as its metaclass.
        """
        return cls._override_class

    @override_class.setter
    def override_class(cls, target_class: Optional[type]):
        if not issubclass(target_class, cls.__class__):
            raise TypeError("Argument cls must be a subclass of OptionHelp")
        cls._override_class = target_class

    # TODO override __call__ so an instance of the configured override_class is
    #  constructed instead of an instance of the given class.


class DryParseHelpType(DryParseType):  # pylint: disable=too-few-public-methods
    """
    Common type for most objects in this module.
    """


class Help(DryParseHelpType, metaclass=_HelpMetaclass):
    """
    Hierarchical representation of a help message. You can customize every
    individual part or subpart of it, or its entirety.
    """

    @reassignable_property
    def text(self):
        """
        The entire help text.

        Overriding this property makes all the other properties obsolete.
        """
        raise NotImplementedError

    text: str

    def __str__(self):
        return self.text  # pylint: disable=no-member

    def __copy__(self):
        _ = None  # prevents the method from being treated as abstract
        raise NotImplementedError


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
        return super().__getattribute__(key)

    @reassignable_property
    def signature(self):
        """
        Describes the command signature when listed as a subcommand in the help
        message of another command.

        Defaults to the command name.
        """
        return Meta(self.command).name

    signature: str

    @reassignable_property
    def desc(self) -> "CommandDescription":  # pylint: disable=no-self-use
        """
        Command description.

        You can assign this to be a ``str`` or :class:`CommandDescription`, but
        you will always get a :class:`CommandDescription` when you try to
        access this as an attribute.
        """
        return CommandDescription("")

    desc: "CommandDescription"

    @reassignable_property
    def sections(self) -> "HelpSectionList":
        """
        Sections of this help message.

        Default implementation returns a standard command section list
        including "usage", "subcommands", etc.
        """
        return self._sections

    sections: "HelpSectionList"

    @reassignable_property
    def section_separator(self):  # pylint: disable=no-self-use
        """Separator between sections of this help message."""
        return "\n\n"

    section_separator: str

    @reassignable_property
    def listing(self):
        """
        Text that appears when this subcommand is listed as a subcommand in the
        help message of another command.
        """
        # pylint: disable=no-member
        meta = Meta(self.command)
        return HelpEntry(meta.name, self.desc.brief).text

    listing: "HelpEntry"

    @reassignable_property
    def text(self):
        return self.section_separator.join(
            sec.text for sec in self.sections if sec.active
        )


class OptionHelp(Help, metaclass=_HelpMetaclass):
    """
    Attributes
    ----------
    override_class: Optional[Type[OptionHelp]]
        When instantiating an object of type :class:`OptionHelp`, return an
        instance of ``override_class`` instead.
    """

    def __init__(self, option: Option):
        self.option = option

    @reassignable_property
    def desc(self):  # pylint: disable=no-self-use
        """Option description."""
        return ""

    desc: str

    @reassignable_property
    def argname(self):
        """Name of the argument to this option."""
        return self.option.long.upper()[2:] or self.option.short.upper()[1:]

    argname: str

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

    signature: str

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

    hint: str

    @reassignable_property
    def text(self):
        # pylint: disable=no-member
        return HelpEntry(self.signature, self.desc).text


class GroupHelp(Help, metaclass=_HelpMetaclass):
    """Help for a :class:`~dryparse.objects.Group` object."""

    def __init__(self, group: AnyGroup):
        self.group = group

    @reassignable_property
    def text(self):
        return ""  # TODO

    text: str


class HelpSection(DryParseHelpType):
    """Help section, with a headline and content."""

    def __init__(self, name_or_group: Union[str, Group]):
        if isinstance(name_or_group, str):
            self.name = name_or_group
        elif isinstance(name_or_group, Group):
            self.group = name_or_group
            self.name = lambda _: name_or_group.name
        else:
            raise TypeError("`name_or_group` must be of type str or Group")

    @reassignable_property
    def name(self) -> str:  # pylint: disable=no-self-use
        """Section name."""
        return ""

    name: str

    @reassignable_property
    def group(self) -> Optional[Group]:
        """:class:`~dryparse.objects.Group` that this section refers to."""
        # pylint: disable=no-self-use
        return None

    group: Optional[Group]

    @reassignable_property
    def headline(self):
        """
        Section headline.

        Default value: ``f"{self.name}:"``.
        """
        return f"{self.name}:"

    headline: str

    @reassignable_property
    def content(self) -> str:  # pylint: disable=no-self-use
        """Section content, excluding headline."""
        return ""

    content: str

    @reassignable_property
    def indent(self):  # pylint: disable=no-self-use
        """Indent for the content of this section."""
        return 2

    indent: int

    @reassignable_property
    def active(self):
        """
        Controls whether the section is displayed.

        Default value: ``True``
        """
        # pylint: disable=no-member
        return bool(self.text)

    active: bool

    @reassignable_property
    def text(self):
        """Entire help text."""
        # pylint: disable=no-member
        return (
            self.headline
            + "\n"
            + textwrap.indent(self.content, " " * self.indent)
        )

    text: str

    def __str__(self):
        return self.text  # pylint: disable=no-member

    def __repr__(self):
        cls = self.__class__
        return (
            f"<{cls.__module__}.{cls.__qualname__}[{repr(self.name)}] "
            f"at {hex(id(self))}>"
        )


class HelpSectionList(List[HelpSection], DryParseHelpType):
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

    def __getitem__(self, item: Union[int, str, Group]):
        # pylint: disable=no-else-return
        if isinstance(item, int):
            return super().__getitem__(item)
        elif isinstance(item, str):
            try:
                return next((sec for sec in self if sec.name == item))
            except StopIteration:
                raise KeyError(item)  # pylint: disable=raise-missing-from
        elif isinstance(item, Group):
            return next((sec for sec in self if sec.group == item))
        else:
            raise TypeError("`item` must be of type str or int")

    def __setattr__(self, key: str, value):
        if not (key.startswith("__") and key.endswith("__")):
            if not hasattr(self, key):
                self.append(value)
            else:
                self[self.index(getattr(self, key))] = value
        super().__setattr__(key, value)

    def __copy__(self):
        new = HelpSectionList(list(self))
        new.__dict__ = copy.copy(self.__dict__)
        return new

    def __deepcopy__(self, memo=None):
        new = HelpSectionList(copy.deepcopy(list(self), memo))
        new.__dict__ = copy.deepcopy(self.__dict__, memo)
        return new


class HelpEntry(DryParseHelpType):
    """
    Represents an option or subcommand entry in a help message.
    """

    __slots__ = ("signature", "desc")

    def __init__(self, signature, desc):
        self.signature = signature
        self.desc = desc

    @reassignable_property
    def signature_width(self):  # pylint: disable=no-self-use
        """
        Width of signature after padding.

        Default: 32 characters.
        """
        return 32

    signature_width: int

    @reassignable_property
    def padded_signature(self):
        """
        Option signature padded until :attr:`signature_width`.
        """
        # pylint: disable=no-member
        return self.signature.ljust(self.signature_width, " ")

    padded_signature: str

    @reassignable_property
    def text(self):
        """Entire help text for this entry."""
        # pylint: disable=no-member
        if self.desc:
            return self.padded_signature + self.desc
        return self.signature

    text: str


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

    __slots__ = ("long", "brief")

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
        """Standard description section for a command."""

        __slots__ = ("command",)

        def __init__(self, command: Command):
            super().__init__("description")
            self.command = command
            self.headline = ""

        @reassignable_property
        def text(self):
            """Entire help text."""
            return Meta(self.command).help.desc.long

        def __str__(self):
            return self.text  # pylint: disable=no-member

        def __repr__(self):
            return object.__repr__(self)

    class UsageSection(HelpSection):
        """Standard usage section for a command."""

        __slots__ = ("command",)

        def __init__(self, command: Command):
            super().__init__("usage")
            self.command = command

        @reassignable_property
        def text(self):
            """Entire help text."""
            meta = Meta(self.command)
            out = StringIO()
            print(
                f"Usage: {meta.name}",
                " ".join(opt.help.hint for opt in meta.options.values()),
                file=out,
                end="",
            )
            return out.getvalue()

        def __str__(self):
            return self.text  # pylint: disable=no-member

        def __repr__(self):
            return object.__repr__(self)

    class CommandsSection(HelpSection):
        """Standard section containing subcommands for a command."""

        __slots__ = ("command",)

        def __init__(self, command: Command):
            super().__init__("Commands")
            self.command = command

        @reassignable_property
        def content(self):
            meta = Meta(self.command)
            return "\n".join(
                tuple(
                    Meta(cmd).help.listing for cmd in meta.subcommands.values()
                )
            )

        @reassignable_property
        def active(self):
            meta = Meta(self.command)
            return bool(meta.subcommands)

    class OptionsSection(HelpSection):
        """Standard section containing options for a command."""

        __slots__ = ("command",)

        def __init__(self, command: Command):
            super().__init__("Options")
            self.command = command

        @reassignable_property
        def content(self):
            meta = Meta(self.command)
            return "\n".join(
                tuple(opt.help.text for opt in meta.options.values())
            )

        @reassignable_property
        def active(self):
            meta = Meta(self.command)
            return bool(meta.options)
