import textwrap

import pytest

from dryparse import Command, parse
from dryparse.errors import CallbackDoesNotSupportAllArgumentsError
from dryparse.objects import (
    Option,
    RootCommand,
    Arguments,
    Meta,
    ResolvedCommand,
)
from dryparse.parser import parse_arg


def create_simple_command():
    cmd = Command("test")
    cmd.opt1 = Option("-1", "--opt", default="opt1_default")
    cmd.opt2 = Option("-2", "--opt2", default="opt2_default", argtype=int)
    cmd.args = Arguments(bool, int)
    return cmd


def create_command_class():
    class MyCommand(Command):
        opt1 = Option("-1", "--opt", default="opt1_default")
        opt2 = Option("-2", "--opt2", default="opt2_default", argtype=int)
        args = Arguments(bool, int)

    return MyCommand


class TestParser:
    def test_parse_option_bool(self):
        cmd = Command("test")
        cmd.version = Option("-v", "--version")
        opt, value = parse_arg(cmd, "--help")
        assert isinstance(opt, Option) and value is None
        opt, value = parse_arg(cmd, "-v")
        assert isinstance(opt, Option) and value is None

    def test_parse_option_string(self):
        cmd = Command("test")
        cmd.output = Option("-o", "--output", argtype=str)
        opt, value = parse_arg(cmd, "-ofile1")
        assert isinstance(opt, Option) and value == "file1"
        opt, value = parse_arg(cmd, "--output=file2")
        assert isinstance(opt, Option) and value == "file2"

    def test_parse_option_with_equals_value(self):
        cmd = Command("test")
        cmd.opt = Option(
            "--opt",
        )

    def test_parse_command_with_options(self):
        cmd = Command("test")
        cmd.random = Option("-r", "--random")
        cmd.output = Option("-o", "--output", argtype=str)
        args = [
            "test",
            "-r",
            "--output",
            "file",
        ]

        cmd = parse(cmd, args)
        assert type(cmd.random) == bool and cmd.random and cmd.output == "file"

    def test_parse_command_help(self, capfd):
        """
        - Construct a command and call it with the ``-h`` option and some
          additional arguments.
        - Verify the contents of the help message
        """
        cmd = Command("test")
        random = Option("-r", "--random")
        cmd.random = random
        random.help.signature = "--random, -r"
        cmd.output = Option("-o", "--output", argtype=str, desc="output file")
        cmd.config = Option(long="--config", argtype=str, argname="FILE")
        args = ["test", "-h", "--random", "positional"]

        cmd = parse(cmd, args)
        cmd()
        cap = capfd.readouterr()
        assert cap.out == textwrap.dedent(
            """\
            Usage: test [-h] [-r] [-o OUTPUT] [--config FILE]

            Options:
              -h, --help                      print help message and exit
              --random, -r
              -o OUTPUT, --output OUTPUT      output file
              --config FILE
            """
        )
        assert not cap.err

    def test_simple_command(self):
        callback_called = False

        cmd = create_simple_command()

        def callback(*args, opt1=None, opt2=None, help=None):
            nonlocal callback_called
            callback_called = True
            assert args == (True, 10)
            assert opt1 == "opt1_default"
            assert opt2 == 2
            assert help is None

        Meta(cmd).set_callback(callback)
        cmd = parse(cmd, ["test", "--opt2", "2", "True", "10"])
        cmd()

        assert callback_called

    def test_invalid_callback_func(self):
        cmd = create_simple_command()
        del cmd.help
        meta = Meta(cmd)

        with pytest.raises(CallbackDoesNotSupportAllArgumentsError):
            meta.set_callback(lambda: ...)
            cmd()
        with pytest.raises(CallbackDoesNotSupportAllArgumentsError):
            meta.set_callback(lambda x, z=1: ...)
            cmd(1, 2, 3)
        with pytest.raises(CallbackDoesNotSupportAllArgumentsError):
            meta.set_callback(lambda z=1: ...)
            cmd(1)


class TestFakeDocker:
    @classmethod
    def setup_class(cls):
        cls.cmd = RootCommand(
            "docker",
            desc="A self-sufficient runtime for containers",
            version="0.1.0",
        )
        cls.cmd.debug = Option("-D", "--debug", desc="Enable debug mode")
        cls.cmd.run = run = Command(
            "run", desc="Run a command in a new container"
        )
        cls.cmd.run.image = Arguments(str)
        cls.cmd.run.command = Arguments(str)
        cls.cmd.run.cmd_args = Arguments((str, ...))
        run.interactive = Option(
            "-i", "--interactive", desc="Keep STDIN open even if not attached"
        )
        run.tty = Option("-t", "--tty", desc="TODO")

    def test_help(self, capfd):
        cmd = parse(self.cmd, ["/usr/bin/docker", "-D", "run", "TODO"])
        cmd
