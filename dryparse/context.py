"""Context information."""
from contextvars import ContextVar

# These would normally be inside the Context class, but the doc says context
# vars should be declared globally.
from typing import List, Optional

_args = ContextVar("args", default=None)
_command_arg_index = ContextVar("command_arg_index", default=0)


class Context:
    """Context information, mainly from the parser."""

    @property
    def args(self) -> Optional[List[str]]:
        """Command line arguments of the current context."""
        return _args.get()

    @args.setter
    def args(self, value: List[str]):
        self._set_var(_args, value)

    @property
    def command_arg_index(self) -> int:
        """Index in :attr:`args` of the currently parsed command."""
        return _command_arg_index.get()

    @command_arg_index.setter
    def command_arg_index(self, value: int):
        self._set_var(_command_arg_index, value)

    def __init__(self, args=None, command_arg_index=None):
        self._reset = {}
        self._args = args
        self._command_arg_index = command_arg_index

    def __enter__(self):
        if self._args is not None:
            self._set_var(_args, self._args)
        if self._command_arg_index is not None:
            self._set_var(_command_arg_index, self._command_arg_index)
        return self

    def __exit__(self, _1, _2, _3):
        for key, token in self._reset.items():
            key.reset(token)
        self._reset.clear()

    def _set_var(self, var: ContextVar, value):
        self._reset[var] = var.set(value)


#: Use this to query context information.
context = Context()
