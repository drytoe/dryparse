"""Internal utils."""
import inspect
from inspect import Parameter
from typing import Callable

from dryparse.errors import SelfNotFirstArgumentError


class NoInit(type):
    """
    Metaclass that doesn't call __init__ automatically when __new__ is
    called on a class.
    """

    def __call__(cls, *args, **kwargs):
        return cls.__new__(cls, *args, **kwargs)


def deepcopy_like_parent(obj: object, memo=None):
    """
    Deep copy ``obj`` using its parent's ``__deepcopy__`` implementation, or
    the default way if it's unimplemented.
    """
    # TODO thread safety
    import copy as copy_module  # pylint: disable=import-outside-toplevel

    class NonExistent:
        """Special marker value."""

    cls = obj.__class__

    # Create temporary snapshots of __copy__ and __deepcopy__ functions
    # on obj and cls, and temporarily remove them from those objects,
    # so their default functionality can be used.
    if hasattr(obj, "__deepcopy__"):
        deepcopy = obj.__deepcopy__
        obj.__deepcopy__ = None
    else:
        deepcopy = NonExistent
    if hasattr(cls, "__deepcopy__"):
        cls_deepcopy = cls.__deepcopy__
        cls.__deepcopy__ = None
    else:
        cls_deepcopy = NonExistent
    if hasattr(obj, "__copy__"):
        copy = obj.__copy__
        obj.__copy__ = None
    else:
        copy = NonExistent
    if hasattr(cls, "__copy__"):
        cls_copy = cls.__copy__
        cls.__copy__ = None
    else:
        cls_copy = NonExistent

    # Create the deep copy
    new = copy_module.deepcopy(obj, memo)

    # Restore __copy__ and __deepcopy__ functions to their versions
    # from the snapshot
    if deepcopy != NonExistent:
        new.__deepcopy__ = deepcopy
    if cls_deepcopy != NonExistent:
        cls.__deepcopy__ = cls_deepcopy
    if copy != NonExistent:
        new.__copy__ = copy
    if cls_copy != NonExistent:
        cls.__copy__ = cls_copy

    return new


def ensure_self_arg(func: Callable):
    """
    Ensure that ``func``'s first argument is ``self``.

    If it isn't, return a wrapper of ``func`` with ``self`` as the first
    argument, and the rest of the signature intact. Otherwise, just return
    ``func``.
    """
    if not inspect.isfunction(func):
        raise NotImplementedError(
            "Not implemented for the case where `func` is a callable that is "
            "not a function"
        )
    sig = inspect.signature(func)
    params = sig.parameters

    if "self" in params:
        if next(iter(params.keys())) != "self":
            raise SelfNotFirstArgumentError
        return func

    modified = lambda self, *args, **kwargs: func(*args, **kwargs)
    params = [Parameter("self", kind=Parameter.POSITIONAL_ONLY)] + list(
        sig.parameters.values()
    )
    modified.__signature__ = sig.replace(parameters=params)
    return modified
