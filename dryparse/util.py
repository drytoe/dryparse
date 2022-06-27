"""Utility functions and objects used throughout dryparse."""
import ast
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
        import copy as copy_module  # pylint: disable=import-outside-toplevel

        def _deepcopy(self_: target_class, memo=None):
            # TODO thread safety
            class NonExistent:
                """Special marker value."""

            # Create temporary snapshots of __copy__ and __deepcopy__ functions
            # on self_ and cls, and temporarily remove them from those objects,
            # so their default functionality can be used.
            if hasattr(self_, "__deepcopy__"):
                deepcopy = self_.__deepcopy__
                self_.__deepcopy__ = None
            else:
                deepcopy = NonExistent
            if hasattr(target_class, "__deepcopy__"):
                cls_deepcopy = target_class.__deepcopy__
                target_class.__deepcopy__ = None
            else:
                cls_deepcopy = NonExistent
            if hasattr(self_, "__copy__"):
                copy = self_.__copy__
                self_.__copy__ = None
            else:
                copy = NonExistent
            if hasattr(target_class, "__copy__"):
                cls_copy = target_class.__copy__
                target_class.__copy__ = None
            else:
                cls_copy = NonExistent

            # Create the deep copy
            new = copy_module.deepcopy(self_, memo)

            # Restore __copy__ and __deepcopy__ functions to their versions
            # from the snapshot
            if deepcopy != NonExistent:
                new.__deepcopy__ = deepcopy
            if cls_deepcopy != NonExistent:
                target_class.__deepcopy__ = cls_deepcopy
            if copy != NonExistent:
                new.__copy__ = copy
            if cls_copy != NonExistent:
                target_class.__copy__ = cls_copy

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
                    prop._instance_overrides[new] = copy_module.deepcopy(
                        prop._instance_overrides[self_]
                    )

            return new

        return _deepcopy
