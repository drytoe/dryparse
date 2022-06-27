"""
Functions for parsing the command line, i.e. converting command line
arguments into their object representations.
"""

import re
import sys
from typing import Any, List, Optional, Tuple, Union

from . import util
from .context import Context
from .errors import (
    OptionDoesNotTakeArgumentsError,
    OptionRequiresArgumentError,
)
from .objects import Command, Meta, Option, ParsedCommand


def parse(command: Command, args: List[str] = None):
    """
    Parse ``args`` into ``command``.

    If unspecified, ``args`` will fall back to ``sys.argv``.
    """
    if args is None:
        args = sys.argv
    with Context() as context:
        if context.args is None:
            context.args = args
            context.command_arg_index = 0
        waiting_for_option_value = False
        option: Optional[Option] = None
        positional_args = []
        option_str: str

        for i, arg in enumerate(args[1:]):
            if waiting_for_option_value:
                option.value = util.parse_str(arg, option.type)
                waiting_for_option_value = False
                continue
            token, value = parse_arg(command, arg)
            if isinstance(token, Option):
                option = token
                if value is not None and option.type != bool:
                    option.value = value
                elif value is not None and option.type == bool:
                    raise OptionDoesNotTakeArgumentsError(arg)
                elif option.type == bool:
                    option.value = True
                else:
                    # The next argument ought to be the option value
                    waiting_for_option_value = True
                    option_str = arg
            elif isinstance(token, Command):
                parse(token, args[i:])
            else:
                positional_args.append(arg)

        if waiting_for_option_value:
            raise OptionRequiresArgumentError(option_str)

    return ParsedCommand(command)


def parse_arg(
    command: Command, arg: str
) -> Union[Tuple[Optional[Option], Optional[Any]], Command]:
    r"""
    Parse ``arg`` using the scheme from ``command``.

    The argument can be an option (or option + value), a positional argument or
    a subcommand. For options, all the usual ways of specifying a CLI option
    are supported:

    - Long version: `--long`/`--long=\<value\>` for bool/non-bool options
    - Short version: `-s`/`-s\<value\>` for bool/non-bool options

    Returns
    -------
    (option, value)
        Option object and its value, or ``None`` if the value was not
        specified in ``arg`` (which means that the value must be found in the
        next argument on the command line, unless it's a bool option).

    Notes
    -----
    - This function does not take into consideration the case when the option
      name is specified as one argument and the option value as another
      argument.
    """
    for opt in Meta(command).options:
        long_re = "^" + opt.long + "(=(.+))?$"
        short_re = "^" + opt.short + "(.+)?"

        # Try to parse ``arg`` as an option
        for regex in long_re, short_re:
            match = re.match(regex, arg)
            if match:
                group = match.groups()[-1]
                if group and opt.type == bool:
                    raise OptionDoesNotTakeArgumentsError(match[0])
                return opt, group

    for cmd in Meta(command).subcommands:
        if re.fullmatch(Meta(cmd).regex, arg):
            return cmd, None

    return None, None
