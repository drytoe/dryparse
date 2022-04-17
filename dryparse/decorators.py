import inspect
from typing import Any, Callable

from docstring_parser.parser import parse

from dryparse.objects import Command


def command(func: Callable[[str], Any]):
    """
    Take a callable and turn it into a :class:`Command` object. The
    function's type hints are used to determine the type.
    """
    cmd = Command(func.__name__, desc=parse(func.__doc__).short_description)
    positional_args = []
    print(inspect.signature(func))
