"""Utility functions and objects used throughout dryparse."""
import ast
import re
from typing import Any, Callable

from dryparse.errors import CallbackDoesNotSupportAllArgumentsError


class _NoInit(type):
    """
    Metaclass that doesn't call __init__ automatically when __new__ is
    called on a class.
    """

    def __call__(cls, *args, **kwargs):
        return cls.__new__(cls, *args, **kwargs)


def parse_str(text: str, target_type: type):
    """Parse string into primitive type ``type``."""
    if target_type == str:
        return text
    obj = ast.literal_eval(text)
    if isinstance(obj, target_type):
        return obj
    return target_type(text)


def first_token_from_regex(regex: str) -> re.Pattern:
    """
    Get first valid token from regular expression ``regex``.

    The first valid token is the smallest substring taken from the beginning of
    ``regex`` that forms a valid regex by itself.
    """
    for i in range(1, len(regex)):
        try:
            return re.compile(regex[0:i])
        except:  # pylint: disable=bare-except
            continue
    return re.compile(regex)


class reassignable_property:
    """
    Property whose getter function can be assigned per instance.

    Caveats
    -------
    - The getter must behave as if its single parameter is the only information
      it knows about the instance that owns this property. This is necessary to
      properly facilitate deep copying. (TODO: enhance and clarify example)

      *Example:*

      >>> class C:
      >>>     @reassignable_property
      >>>     def prop(self):
      >>>         return "default_value"
      >>>
      >>>     def __init__(self, value):
      >>>         self.value = value
      >>>         # Correct:
      >>>         self.prop = lambda self_: self_.value
      >>>         # Wrong:
      >>>         self.prop = lambda _: self.value
    """

    def __init__(self, getter: Callable[[Any], Any]):
        self.getter = getter
        self.name = None
        self.__doc__ = getter.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(
            self.name, getattr(owner, self.name)
        ).getter(instance)

    def __set__(self, instance, value_or_getter: Callable[[Any], Any]):
        if isinstance(value_or_getter, Callable):
            getter = value_or_getter
        else:
            getter = lambda _: value_or_getter
        instance.__dict__[self.name] = reassignable_property(getter)

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def __set_name__(self, owner, name):
        self.name = name


def verify_function_callable(func, *args, **kwargs):
    """
    Verify if ``func(*args, **kwargs)`` is a valid call without actually
    calling the function. If yes, do nothing, else raise an exception.

    Raises
    ------
    dryparse.errors.CallbackDoesNotSupportAllArgumentsError
        If the verification fails.
    """
    from inspect import Signature  # pylint: disable=import-outside-toplevel

    try:
        Signature.from_callable(func).bind(*args, **kwargs)
    except TypeError as e:
        raise CallbackDoesNotSupportAllArgumentsError from e
