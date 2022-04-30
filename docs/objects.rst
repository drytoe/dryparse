Object model
============

.. toctree::

The decorators are useful for commands that are simple and follow basic CLI
conventions. Sometimes you want to extend your CLI with custom features. This is
where the object model comes in.

Each concept in a commandline program is represented by an object in the
:data:`dryparse.objects` module. In that vein, each command is represented by an
instance of :class:`dryparse.objects.Command`, each option by a
:class:`dryparse.objects.Option`.

.. doctest::

   >>> git = Command("git")
