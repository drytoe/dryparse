================
Customizing help
================

.. toctree::

Dryparse generates standard help out of the box, but it also provides a
hierarchical representation of a help message via :class:`~dryparse.help.Help`.
You can obtain a help object for any of: :class:`~dryparse.objects.Command`,
:class:`~dryparse.objects.Option`, :class:`~dryparse.objects.Group`.

.. todo:: Group help is not implemented yet.

.. autolink-preface:: from dryparse.help import Help

.. code:: python

   git_help = Meta(git).help
   dryparse.parse()

For example, the default help message for the `git` subcommand we've been
building so far would be:

.. code::

 A version control software

 Usage: git [-h] []

You can easily convert this to a help message string using:

.. code:: python

   str(git_help)
   # or
   git_help.text

