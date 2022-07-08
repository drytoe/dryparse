"""The decorator API."""

import inspect
from inspect import Parameter
from typing import Any, Callable

from docstring_parser import Docstring
from docstring_parser.parser import parse

from dryparse.errors import (
    AnnotationMustBeTypeOrSpecialError,
    VariadicKwargsNotAllowedError,
)
from dryparse.objects import Arguments, Command, Meta, Option

__all__ = ("command", "subcommand")


def command(func: Callable[..., Any]):
    """
    Take a callable and turn it into a :class:`~dryparse.objects.Command`
    object.

    Each positional argument will be converted to an
    :class:`~dryparse.objects.Arguments` object whose
    :attr:`~dryparse.objects.Arguments.pattern` will be generated using the
    type annotation.

    Each keyword argument will be converted to an
    :class:`~dryparse.objects.Option` object, again using the information from
    the type annotation. If the annotation is an instance of
    :class:`~dryparse.objects.Option`, this instance will be used directly.

    **IMPORTANT**: Type annotations must be actual types and not ``Union``,
    ``Any`` etc. This is required because the type will used to convert CLI
    arguments into their Python representations. *As a special case*, the
    annotation for keyword arguments can be an instance of
    :class:`~dryparse.objects.Option`.

    Notes
    -----
    - ``func`` will become the :class:`~dryparse.objects.Meta.call` attribute
      associated with the :class:`~dryparse.objects.Command` object returned by
      this decorator. You should read the documentation of
      :class:`~dryparse.objects.Meta.call`.
    - If a parameter is neither annotated nor has a default value, its type is
      assumed to be ``str``.
    - The text for specifying an option on the command line is derived from the
      argument name in the following way:

      - The short text is formed by prepending a `-` before the first character
        of the argument name. Note that
        if multiple argument names start with the same character, only the
        first one will get a short text.

        *Example:* ``recursive`` becomes `-r`.

      - The long text is formed by prepending `--` before the argument name,
        additionally replacing all ``_`` characters with `-`.

        *Example:* ``work_dir`` becomes `--work-dir`.

    Raises
    ------
    :class:`~dryparse.errors.AnnotationMustBeTypeOrSpecialError`
        If a type annotation is not a ``type``, or an instance of
        :class:`~dryparse.objects.Option`, the latter only being allowed for
        keyword arguments.

    See Also
    --------
    dryparse.objects.Meta.call
    """
    doc = parse(func.__doc__)

    cmd = Command(func.__name__, desc=doc.short_description)
    signature = inspect.signature(func)

    params = signature.parameters.values()
    iter_params = iter(params)

    # A first parameter named 'self' is special - do not generate an
    # Argument/Option from it
    first_param = next(iter(params), None)
    if first_param and first_param.name == "self":
        next(iter_params)

    for param in iter_params:
        if param.kind == Parameter.POSITIONAL_ONLY or (
            param.kind == Parameter.POSITIONAL_OR_KEYWORD
            and param.default == Parameter.empty
        ):
            if not isinstance(param.annotation, type):
                raise AnnotationMustBeTypeOrSpecialError(param)
            setattr(cmd, param.name, Arguments(param.annotation))
        elif param.kind == Parameter.VAR_POSITIONAL:
            if not isinstance(param.annotation, type):
                raise AnnotationMustBeTypeOrSpecialError(param)
            setattr(cmd, param.name, Arguments((param.annotation, ...)))
        elif param.kind == Parameter.KEYWORD_ONLY or (
            param.kind == Parameter.POSITIONAL_OR_KEYWORD
            and param.default != Parameter.empty
        ):
            if not isinstance(param.annotation, (type, Option)):
                raise AnnotationMustBeTypeOrSpecialError(param)
            setattr(cmd, param.name, _option_from_parameter(param, doc))
        elif param.kind == Parameter.VAR_KEYWORD:
            raise VariadicKwargsNotAllowedError

    Meta(cmd).call = func
    return cmd


def subcommand(func: Callable[[Command], Any]):
    """Decorator used to register a subcommand inside a class's context."""
    _ = func  # TODO


def _get_annotation(parameter: Parameter):
    return (
        parameter.annotation
        if parameter.annotation != Parameter.empty
        else type(parameter.default)
        if parameter.default != Parameter.empty
        else str
    )


def _option_from_parameter(param: Parameter, doc: Docstring):
    # TODO in case of conflict only the first option should get a short text
    if isinstance(param.annotation, Option):
        return param.annotation
    name = param.name
    annotation = _get_annotation(param)
    return Option(
        short=f"-{name[0]}",
        long=f"--{name.replace('_', '-')}",
        argname=name.upper(),
        default=param.default if param.default != Parameter.empty else None,
        argtype=annotation,
        desc=doc.short_description,
    )
