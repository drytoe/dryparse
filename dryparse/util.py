import ast
import inspect
import re
import weakref
from typing import Any, Callable


class _NoInit(type):
    """
    Metaclass that doesn't call __init__ automatically when __new__ is
    called on a class.
    """

    def __call__(cls, *args, **kwargs):
        return cls.__new__(cls, *args, **kwargs)


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


class reassignable_property:
    """Property whose getter function can be assigned per instance."""

    def __init__(self, getter: Callable[[Any], Any]):
        self.getter = getter
        # Maps each instance to an overridden getter for this property. If an
        # instance is missing from this dict, the default value is used.
        self._instance_overrides: weakref.WeakKeyDictionary[
            Any, Callable[[Any], Any]
        ] = weakref.WeakKeyDictionary()
        self.__doc__ = getter.__doc__

    def __get__(self, instance, owner):
        if instance in self._instance_overrides:
            return self._instance_overrides[instance](instance)
        return self.getter(instance)

    def __set__(self, instance, value_or_getter: Callable[[Any], Any]):
        if isinstance(value_or_getter, Callable):
            self._instance_overrides[instance] = value_or_getter
        else:
            self._instance_overrides[instance] = lambda _: value_or_getter

    def __delete__(self, instance):
        del self._instance_overrides[instance]
