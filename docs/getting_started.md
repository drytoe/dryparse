# Getting started

```{toctree}
```

## Installation

```{prompt} bash
pip install dryparse
```

## If you have used a CLI parser library before...

... you can just skim over the code blocks in this *Getting started* section.
You should immediately get a sense of what is happening. But you shouldn't skip
the {ref}`Object model` and {ref}`Customizing help` sections, or you'll miss
out on the true power of `dryparse`! For those of you who have used
[typer](https://typer.tiangolo.com), this section should feel very familiar.

## Creating a simple command

````{collapse} TL; DR (complete code for this section)
   ```{code-block}
   :emphasize-lines: 7,8,17,19
   
   #!/usr/bin/env python3
   import dryparse
   
   # 1. Define a command using a function.
   # - `files` are positional arguments
   # - Keyword arguments get translated into options: `format`, `terse`
   @dryparse.command
   def stat(*files, format: str = None, terse=False):
       print("stat command called with:")
       print("  files:", *files)
       print("  format:", format)
       print("  terse:", terse)
   
   if __name__ == "__main__":
       # 2. Parse the command line arguments according to the command
       #    specification of `stat`
       cmd = dryparse.parse(stat)
       # 3. Execute the command
       cmd()
   ```
   
   For reference, running `python __main__.py --help` will print the following
   help message:
   
   ```text
   Usage: stat [-h] [-r] [-f] [files...]
   
   Arguments:
     [files...]
   
   Options:
     -h, --help                      print help message and exit
     -f, --format
     -t, --terse
   ```
   
   <hr />
````

<br />

Let's create a simplified GNU `stat` command.

```
import dryparse

@dryparse.command
def stat(*files, format: str = None, terse=False):
    # The implementation is not important at the moment
    pass
```

```{hint}
Click on ``dryparse.command`` in the above code block to go to its API
documentation. Whenever you see a ``dryparse`` member in a code block, you can
try clicking on it to view its API documentation.
```

Using the code above, we have defined a command named `stat` that takes zero or
more files as positional (required) arguments, and two options.

The ``format`` option is specified on the command line as `-f` or `--format`
and the ``terse`` option as `-t` or `--terse`. We'll see later how we can
customize that.

Since we didn't annotate ``files``, they are taken to be strings (``str``) by
default. The ``format`` option accepts a value of type ``str`` because of the
type hint we used. The ``terse`` option is a ``bool`` and doesn't take any
arguments on the command line (if `-t`/`--terse` is present on the command
line, it will make ``terse`` equal to ``True``).

In your main script (`__main__.py` or otherwise), add the following code to
parse the CLI arguments passed to your script:

```
# Reads CLI args from `sys.argv` and validates them against the `stat`
# command. Returns a command object that can be called to execute the command.
cmd = dryparse.parse(stat)
```

To execute the command simply add this:

```
cmd()
```

In summary, when someone calls your script like
{any}`python path/to/your/script.py <arguments>`, the code above will:

- Validate the arguments and raise appropriate errors if something's wrong
- Execute the command based on the given arguments

## Adding help

An undocumented command line program is not very useful. So let's document it.

All you have to do is add a docstring -- {attr}`dryparse.command<dryparse.decorators.command>`
will read it and generate a help message based on that.

`````{tabs}

   ````{tab} Source
      ```{code-block}
      :emphasize-lines: 3-8

      @dryparse.command
      def stat(*files, format: str = None, terse=False):
          """Display file or file system status.

          :param files: files whose info we want to know
          :param format: use the specified FORMAT instead of the default
          :param terse: print the information in terse form
          """
          ...
      ```
   ````

   ````{tab} Resulting help text
      **Command**

      ```{prompt} bash
      python __main__.py --help
      ```

      **Output**

      ```text
      Display file or file system status.

      Usage: stat [-h] [-f FORMAT] [-t] [files...]

      Arguments:
        [files...]                      files whose info we want to know

      Options:
        -h, --help                      print help message and exit
        -f FORMAT, --format FORMAT      use the specified FORMAT instead of the default
        -t, --terse                     print the information in terse form
      ```
`````

The help message generated by `dryparse` is based on established practices for
CLI programs, but you can fully customize it. Read {ref}`Customizing help` for
details.

## Argument validation

```{todo}
Finish this section.
```

While you can validate options and arguments within the ``stat`` function,
sometimes it's better and more maintainable for the annotated types to serve as
validators. For example, in the following code

## Customizing the CLI

You might notice that the short version of the {any}`--format` option of GNU
{any}`stat` is {any}`-c`, and not the {any}`-f` that dryparse generated for us.
We can add more specifics to options by annotating them with
{class}`~dryparse.objects.Option`.

```{code-block}
:emphasize-lines: 3

def stat(
    *files,
    format: Option("-c", "--format", argtype=str) = None,
    terse=False
):
    """Display file or file system status.

    :param files: files whose info we want to know
    :param format: use the specified FORMAT instead of the default
    :param terse: print the information in terse form
    """
    ...
```

The same goes for positional arguments. For example, some CLI programs like to
display positional argument names in all caps in their help messages. We can
easily do this by annotating ``files`` with
{class}`~dryparse.objects.Arguments`. Since we want to change the name, we
will add a ``name`` keyword argument.

```{code-block}
:emphasize-lines: 2

def stat(
    *files: Arguments(name="FILES"),
    format: Option("-c", "--format", argtype=str) = None,
    terse=False
):
    """Display file or file system status.

    :param files: files whose info we want to know
    :param format: use the specified FORMAT instead of the default
    :param terse: print the information in terse form
    """
    ...
```

```{note}
We recommend that you look at the API documentation of
{class}`~dryparse.objects.Option` and {class}`~dryparse.objects.Arguments` to
see what you can do with them. Or even better, have a look at the
{ref}`Object model` section that explains them in a detailed but approachable
way.
```

## Adding a subcommand

Functions decorated with {attr}`dryparse.command<dryparse.decorators.command>`
get transformed into objects of type {class}`~dryparse.objects.Command`.
Positional arguments and options exist as attributes of these objects. You can
find out more about this in {ref}`Object model`.

Subcommands are no different. You can add a subcommand by adding an attribute
to an existing command:

```{code-block}
:emphasize-lines: 9

@dryparse.command
def command(option1=None, option2=None):
    ...

@dryparse.command
def subcommand(option=None):
    ...

command.subcommand = subcommand
```

You can nest subcommands as you please:

```
command.subcommand = subcommand
subcommand.subsubcommand = subsubcommand
```

## Next steps

We have so far explored the simplest way to create a command -- by defining a
function and decorating it with
{attr}`dryparse.command<dryparse.decorators.command>`. But `dryparse` offers
much more powerful and flexible ways as well.
