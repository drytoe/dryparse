"""
Functions for parsing the command line, i.e. converting command line
arguments into their object representations.
"""
import copy
import re
import sys
from typing import Any, Iterable, List, Optional, Tuple, Union

from . import util
from .context import Context
from .errors import (
    NotEnoughPositionalArgumentsError,
    OptionDoesNotTakeArgumentsError,
    OptionRequiresArgumentError,
    TooManyPositionalArgumentsError,
)
from .objects import Arguments, Command, Meta, Option, ResolvedCommand

__all__ = ("parse", "parse_arg")


def parse(command: Command, args: List[str] = None):
    """
    Parse ``args`` into ``command``.

    If unspecified, ``args`` will fall back to ``sys.argv``.
    """
    cmd = copy.deepcopy(command)
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
            token, value = parse_arg(cmd, arg)
            if isinstance(token, Option):
                option = token
                if value is not None and option.type != bool:
                    option.value = util.parse_str(value, option.type)
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
                return ResolvedCommand(cmd, deepcopy=False)
            else:
                positional_args.append(arg)

        if waiting_for_option_value:
            raise OptionRequiresArgumentError(option_str)

        parsed_arg_count = _distribute_args_into_buckets(
            positional_args, Meta(cmd).argument_aliases.values()
        )

        # Put all positional argument into cmd's arguments of type `Arguments`
        if parsed_arg_count > len(positional_args):
            raise NotEnoughPositionalArgumentsError
        if parsed_arg_count < len(positional_args):
            raise TooManyPositionalArgumentsError

    return ResolvedCommand(cmd, deepcopy=False)


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
    for opt in Meta(command).options.values():
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

    for cmd in Meta(command).subcommands.values():
        if re.fullmatch(Meta(cmd).regex, arg):
            return cmd, None

    return None, None


def _distribute_args_into_buckets(
    args: List[str], arg_buckets: Iterable[Arguments]
):
    """
    Returns
    -------
    Number of arguments that were successfully distributed.
    """
    arg_index = 0
    for arg_bucket in arg_buckets:
        arg_bucket: Arguments
        converted = arg_bucket.assign(args[arg_index:], allow_extra_args=True)
        arg_index += len(converted)

    return arg_index
