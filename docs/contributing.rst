============
Contributing
============

.. toctree::

Programming techniques you should keep in mind
==============================================

Marking a method as unimplemented but not abstract
--------------------------------------------------

.. code:: python

   def method(self):
      ...  # pylint: unnecessary-ellipsis
      raise NotImplementedError

Documentation
=============

- Shell code must be added like this:

.. code:: rst

   .. prompt:: bash

      shell commands here

- When adding python code examples, dryparse objects must link to their
  corresponding documentation:

     .. tabs::

        .. tab:: Correct

           Source:
              .. code:: rst

                 .. autolink-preface:: from dryparse.objects import Command

                 .. code:: python

                    cmd = Command("test")
           Result:
              .. autolink-preface:: from dryparse.objects import Command

              .. code:: python

                 cmd = Command("test")

        .. tab:: Wrong

           Source:
              .. code:: rst

                 .. code:: python

                    cmd = Command("test")
           Result:
              .. autolink-skip:: next

              .. code:: python

                 cmd = Command("test")

     For more info, see the documentation of `sphinx-codeautolink <https://sphinx-codeautolink.readthedocs.io>`_.
