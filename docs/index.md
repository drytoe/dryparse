# Welcome to dryparse's documentation!

```{toctree}
:maxdepth: 2
:hidden:

getting_started.md
objects.md
customizing_help.md
custom_parsing.md
api/index.md
contributing.md
```

In a nutshell, dryparse is a CLI parser that makes it easy to turn regular
functions and objects into command line commands and options. It works out of
the box, with default behaviors that follow established practices. In addition,
it provides excellent customizability and an object model that gives you the
power to do anything you want with it.

As an appetizer, let's try to recreate the ubiquitous `cp` command:

```{autolink-preface}
import dryparse
```

```
@dryparse.command
def cp(
   *files, link=False, force=False, target_directory: str = None
):
   """
   Copy files and directories
   """
   ... # Logic goes here

```
Do this in your program's entrypoint:

```
cmd = dryparse.parse(cp, sys.argv)
cmd()
```

When someone runs this in the shell:

```
cp --link -r --target-directory "/tmp/" source/ b.txt
```

this will run in the python world:

```
cp("source/", "b.txt", link=True, recursive=True, target_directory="/tmp/")
```

This works out of the box too (help is automatically generated from the function
docstring):

```{prompt} bash
cp --help
```

A more holistic example:

```{prompt} bash
docker run -ite ENVVAR1=1 --env ENVVAR2=2 \
   --volume=/:/mnt:ro -v /home:/h         \
   alpine sh
```

```{hint}
`-i` is short for `--interactive` <br />
`-t` is short for `--tty` <br />
`-e` is short for `--env` <br />
`-v` is short for `--volume`
```

```
docker.run("alpine", "sh",
           interactive=True,
           tty=True,
           env=[("ENVVAR1", "1"), ("ENVVAR2", "2")],
           volume=[("/", "/mnt", "ro"), ("/home", "/h")])
```

## Problems

- When a command contains a subcommand and option with the same name

```{todo} Structure
- Walkthrough
- Topic-based guide
- Advanced use cases
- Api
```
