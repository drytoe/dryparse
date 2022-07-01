"""Internal utils."""


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
