Welcome to dryparse's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :hidden:

   api/index.rst
   objects.rst

Dryparse attempts to minimize the abstraction between a command invocation and a
python function call. For example:

.. code-block:: shell

   git --help

is most elegantly represented in python as a function call:

.. code-block:: python

   git(help=True)

A more holistic example:

.. code-block:: shell

   docker run -ite ENVVAR1=1 --env ENVVAR2=2 \
      --volume=/:/mnt:ro -v /home:/h         \
      alpine sh

.. hint::

   | `-i` is short for `--interactive`
   | `-t` is short for `--tty`
   | `-e` is short for `--env`
   | `-v` is short for `--volume`

.. code-block:: python

   docker.run("alpine", "sh",
              interactive=True,
              tty=True,
              env=[("ENVVAR1", "1"), ("ENVVAR2", "2")],
              volume=[("/", "/mnt", "ro"), ("/home", "/h")])

Problems
--------

- When a command contains a subcommand and option with the same name


.. todo:: Structure

   - Walkthrough
   - Topic-based guide
   - Advanced use cases
   - Api
