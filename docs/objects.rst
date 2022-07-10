.. comment::
   NOTE: The examples used here are essentially a decomposition of docs/examples/git.py,
   which contains the full example and is runnable and testable. Keep this
   example up to date with that file.

============
Object model
============

.. toctree::

The decorators are useful for commands that are simple and follow basic CLI
conventions. Sometimes you want to extend your CLI with custom features. This is
where the object model comes in.

Each concept in a commandline program is represented by an object in the
:data:`dryparse.objects` module. Thus, each command is represented by an
instance of :class:`~dryparse.objects.Command`, each option by an
:class:`~dryparse.objects.Option`, etc.

The fundamentals
================

The simplest way to create a command is:

.. autolink-preface::

   from dryparse.objects import *
   from dryparse.help import *

.. code:: python

   git = Command("git", desc="A version control software")

Adding options is super easy:

.. code:: python

   git.paginate = Option("-p", "--paginate")

.. note::

   The ``git.paginate`` attribute didn't exist before. We created it dynamically by assigning a value to it.

By default, options have a type of ``bool``. This means that when the option is
specified on the command line it will have a value of ``True``, and ``False``
otherwise.

Let's create an option of type ``int``:

.. code:: python

   git.retries = Option("-r", "--retries", type=int)

This option will expect an argument to be specified via the command line. The
argument is automatically converted to the type we specified (in this case
``int``).

.. note::

   All options except for ``bool`` and some :ref:`special types<dryparse.types>`
   take CLI arguments, and those arguments are automatically converted to the
   specified type.

Note that commands include a `--help` option by default, via a ``help``
attribute that is just like any other attribute. You can delete it if you don't need it:

.. code:: python

   del git.help

Adding a subcommand
===================

Adding a subcommand is just as easy as adding an option:

.. code:: python

   git.commit = Command("commit", desc="Record changes to the repository")
   git.checkout = Command("checkout", desc="Switch branches or restore working tree files")

Defining positional arguments
=============================

.. code:: python

   git.add.args = Arguments((str, ...))

These use cases are simple, but we support so many more. Take a look at the API
documentation of :class:`~dryparse.objects.Arguments`, especially the
**Examples** section.

Root command
============

CLI programs usually include a `--version` option in their root command. While
you can add this option yourself, we provide :class:`~dryparse.objects.RootCommand` as a convenience:

.. code:: python

   git = RootCommand("git", version="0.1.0", desc="A version control software")
