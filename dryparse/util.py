import ast
import re
from io import StringIO
from itertools import chain
from typing import Iterator, List, Type, Union

# TODO remove
from dryparse.objects import Meta


class _OptionContainer:
    def __init__(self):
        from .objects import Option

        self.options: List[Option] = []

    def __getitem__(self, arg: str):
        """Get the option that matches the CLI argument ``arg``."""
        for opt in self.options:
            if (opt.short and re.match(opt.short, arg)) or (
                opt.long and re.match(opt.long, arg)
            ):
                return opt
        raise KeyError(arg)

    def add(self, option: "Option"):
        self.options.append(option)

    def remove(self, option: "Option"):
        self.options.remove(option)

    def __iter__(self) -> Iterator["Option"]:
        yield from self.options

    def __contains__(self, option: str):
        try:
            self.__getitem__(option)
            return True
        except KeyError:
            return False

    def __bool__(self):
        return bool(self.options)

    @staticmethod
    def _get_match(regex, arg):
        """
        Verify that ``regex`` represents an option specified via  the CLI argument ``arg``
        """
        regex = regex + "(=(.*))"
        return


def get_help(command: "Command"):
    from .objects import Command

    command: Command
    meta = Meta(command)
    out = StringIO()
    print_ = lambda *args, **kwargs: print(*args, file=out, **kwargs)
    print_(
        f"Usage: {meta.name}",
        " ".join(opt.hint for opt in meta.options),
    )
    print_()

    # Calculate max length for proper alignment
    opt_max_length = max(
        chain([0], (len(opt.signature) for opt in meta.options))
    )
    cmd_max_length = max(
        chain([0], (len(Meta(cmd).name) for cmd in meta.subcommands))
    )
    max_length = min(max(22, opt_max_length, cmd_max_length), 48)

    if meta.options:
        print_("Options:")

    for opt in meta.options:
        print_(" ", (opt.signature.ljust(max_length + 2) + opt.help).strip())

    if meta.subcommands:
        if meta.options:
            print_()
        print_("Commands:")
    for cmd in meta.subcommands:
        print_(" ", Meta(cmd).name.ljust(max_length), Meta(cmd).desc)

    return out.getvalue()[:-1]  # Remove newline at the end


def parse_str(text: str, type: type):
    """Parse string into primitive type ``type``."""
    if type == str:
        return text
    obj = ast.literal_eval(text)
    if isinstance(obj, type):
        return obj
    else:
        return type(text)


def first_token_from_regex(regex: str) -> re.Pattern:
    for i in range(1, len(regex)):
        try:
            return re.compile(regex[0:i])
        except:
            continue
    return re.compile(regex)
