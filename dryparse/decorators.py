import inspect
from typing import Any, Callable

from docstring_parser.parser import parse

from dryparse.objects import Command


def command(func: Callable[[str], Any]):
    """
    Take a callable and turn it into a :class:`Command` object. The
    function's type hints are used to determine the type.
    """
    doc = parse(func.__doc__)
    cmd = Command(func.__name__, desc=doc.short_description)
    positional_args = []
    print(inspect.signature(func))

    return cmd


def subcommand(func: Callable[[Command], Any]):
    pass
