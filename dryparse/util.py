"""Utility functions and objects used throughout dryparse."""
import ast
import re
import weakref
from typing import Any, Callable

from dryparse._util import deepcopy_like_parent
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
    - In order to be properly deep-copyable, objects containing reassignable
      properties must call :meth:`reassignable_property.deepcopy_func` within
      their ``__deepcopy__`` implementation.
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
        # Maps each instance to an overridden getter for this property. If an
        # instance is missing from this dict, the default value is used.
        self._instance_overrides: weakref.WeakKeyDictionary[
            Any, Callable[[Any], Any]
        ] = weakref.WeakKeyDictionary()
        self.__doc__ = getter.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
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

    @staticmethod
    def deepcopy_func(target_class: type):
        """
        A utility function that will deepcopy an object of class
        ``target_class`` in the usual way, along with its reassignable
        properties.

        Usage
        -----
        In a class that wants to implement the deepcopy operation, implement
        ``__deepcopy__`` such that it calls this function in turn.

        >>> class C:
        >>>     @reassignable_property
        >>>     def prop(self):
        >>>         return "prop_value"
        >>>
        >>>     def __deepcopy__(self, memo=None):
        >>>         func = reassignable_property.deepcopy_func(self.__class__)
        >>>         new_obj = func(self, memo)
        >>>         # Custom, supplementary deepcopy logic...
        >>>         return new_obj

        Notes
        -----
        The copy operation performed by this function will honor the
        implementations of ``__deepcopy__`` by the parent classes of
        ``target_class``.
        """
        import copy  # pylint: disable=import-outside-toplevel

        def _deepcopy(self_: target_class, memo=None):
            new = deepcopy_like_parent(self_, memo)
            # Supplement the default deepcopy by copying reassignable
            # properties too.
            for name in dir(target_class):
                # pylint: disable=protected-access
                prop = getattr(target_class, name)
                if (
                    not (name.startswith("__") and name.startswith("__"))
                    and isinstance(prop, reassignable_property)
                    and self_ in prop._instance_overrides
                ):
                    prop._instance_overrides[new] = copy.deepcopy(
                        prop._instance_overrides[self_]
                    )

            return new

        return _deepcopy


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
