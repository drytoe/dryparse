"""The decorator API."""

import inspect
from inspect import Parameter
from symbol import decorator
from types import FunctionType, ModuleType
from typing import Any, Callable, Type, TypeVar, Union, overload

from docstring_parser import Docstring
from docstring_parser.parser import parse

from dryparse.errors import (
    AnnotationMustBeTypeOrSpecialError,
    VariadicKwargsNotAllowedError,
)
from dryparse.help import Description
from dryparse.objects import Arguments, Command, DryParseType, Meta, Option

__all__ = ("command", "subcommand")

_SubclassOfCommand = TypeVar("_SubclassOfCommand", bound=Command)


class command:
    """
    Return a :class:`~dryparse.objects.Command` object created from the passed
    argument.

    A call to this class will in turn call one of: :any:`from_function`,
    :any:`from_class` or :any:`from_module` based on the type of the argument.
    You should read the documentation of whichever one of those is applicable.

    This class should is meant to be used as a decorator.

    Parameters
    ----------
    obj
        Object from which to create a :class:`~dryparse.objects.Command`. This
        can be a function, a subclass of :class:`~dryparse.objects.Command` or
        a module.
    """

    _Any = Union[FunctionType, Type[Command], ModuleType]

    def __init__(self, obj: _Any):
        # pylint: disable=super-init-not-called
        pass

    def __new__(cls, obj: _Any):
        if inspect.isfunction(obj):
            return cls.from_function(obj)
        if isinstance(obj, Command):
            return obj
        if isinstance(obj, type) and issubclass(obj, Command):
            return cls.from_class(obj)
        if isinstance(obj, ModuleType):
            return cls.from_module(obj)

    @classmethod
    def from_function(cls, func: FunctionType):
        """
        Create a :class:`~dryparse.object.Command` object with ``func`` as
        its callback.

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
        - ``func`` will become the :class:`~dryparse.objects.Meta.call`
          attribute associated with the :class:`~dryparse.objects.Command`
          object returned by this decorator. You should read the documentation
          of :class:`~dryparse.objects.Meta.call`.
        - If a parameter is neither annotated nor has a default value, its type
          is assumed to be ``str``.
        - The text for specifying an option on the command line is derived from
          the argument name in the following way:

          - The short text is formed by prepending a `-` before the first
            character of the argument name. Note that if multiple argument
            names start with the same character, only the first one will get a
            short text.

            *Example:* ``recursive`` becomes `-r`.

          - The long text is formed by prepending `--` before the argument
            name, additionally replacing all ``_`` characters with `-`.

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
        cmd, doc = cls._command_with_copied_docstring(func)
        signature = inspect.signature(func)

        params = signature.parameters.values()
        iter_params = iter(params)

        # A first parameter named 'self' is special - do not generate an
        # Argument/Option from it
        first_param = next(iter(params), None)
        if first_param and first_param.name == "self":
            next(iter_params)

        for param in iter_params:
            annotation = (
                param.annotation
                if param.annotation != Parameter.empty
                else None
            )
            if param.kind == Parameter.POSITIONAL_ONLY or (
                param.kind == Parameter.POSITIONAL_OR_KEYWORD
                and param.default == Parameter.empty
            ):
                if not isinstance(param.annotation, type):
                    raise AnnotationMustBeTypeOrSpecialError(param)
                setattr(cmd, param.name, Arguments(annotation or str))
            elif param.kind == Parameter.VAR_POSITIONAL:
                if not isinstance(param.annotation, type):
                    raise AnnotationMustBeTypeOrSpecialError(param)
                setattr(cmd, param.name, Arguments((annotation or str, ...)))
            elif param.kind == Parameter.KEYWORD_ONLY or (
                param.kind == Parameter.POSITIONAL_OR_KEYWORD
                and param.default != Parameter.empty
            ):
                if not isinstance(param.annotation, (type, Option)):
                    raise AnnotationMustBeTypeOrSpecialError(param)
                setattr(cmd, param.name, _option_from_parameter(param, doc))
            elif param.kind == Parameter.VAR_KEYWORD:
                raise VariadicKwargsNotAllowedError

        _fill_help_based_on_docstring(cmd, doc)

        Meta(cmd).call = func
        return cmd

    """
    @classmethod
    @overload
    def from_class(
        cls, class_: Type[_SubclassOfCommand]
    ) -> _SubclassOfCommand:
        ...
    """

    @classmethod
    def from_class(cls, class_: Type[Command]):
        """
        Create a :class:`~dryparse.objects.Command` by intantiating ``class_``.

        While creating the command, ``class_``'s docstring will be used to
        populate the help message of the created command. The command's name
        will match ``class_.__name__``.
        """
        cmd, doc = cls._command_with_copied_docstring(class_)
        if issubclass(class_, Command):
            return cmd
        for name in dir(class_):
            if name.startswith("_"):
                continue
            attr = getattr(class_, name)
            if isinstance(attr, DryParseType):
                continue
            if isinstance(attr, (FunctionType, type, ModuleType)):
                setattr(cmd, name, cls(attr))
        return cmd

    @classmethod
    def from_module(cls, mod: ModuleType):
        """TODO"""
        pass

    @classmethod
    def _command_with_copied_docstring(cls, obj: _Any):
        doc = parse(obj.__doc__)
        class_ = (
            obj
            if isinstance(obj, type) and issubclass(obj, Command)
            else Command
        )

        cmd = class_(
            obj.__name__,
            desc=Description(
                (
                    doc.short_description
                    + ("\n\n" if doc.long_description else "")
                    if doc.short_description
                    else ""
                )
                + (doc.long_description or ""),
                brief=doc.short_description,
            ),
        )

        return cmd, doc


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


def _fill_help_based_on_docstring(cmd: Command, doc: Docstring):
    # TODO what about params in docstring that don't exist in function sig?
    for param in doc.params:
        name = param.arg_name
        desc = param.description
        attr = getattr(cmd, name)
        if isinstance(attr, Option):
            if "default" not in desc and attr.value is not None:
                desc += f" (default: {repr(attr.value)})"
            attr.help.desc = desc
        elif isinstance(attr, Arguments):
            attr.help.desc = desc
