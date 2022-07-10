import textwrap

import dryparse
from dryparse.objects import Option, Arguments, Meta


def create_cp_command():
    @dryparse.command
    def cp(source: str, dest: str, *, recursive=False):
        _ = source, dest, recursive

    return cp


class TestCommandDecorator:
    manually_created_option: Option = None

    @classmethod
    def setup_class(cls):
        cls.manually_created_option = Option("-O", "--Opt4")

    def test_command_creation_empty(self):
        """Command with no arguments or options (except default `help`)."""

        @dryparse.command
        def cmd1():
            pass

        @dryparse.command
        def cmd2(self):
            _ = self

        assert list(cmd1.__dict__.keys()) == ["help"]
        assert list(cmd2.__dict__.keys()) == ["help"]

    def test_command_creation_simple(self):
        @dryparse.command
        def cmd(arg1: str, arg2: int, o: int = None, p: str = "a"):
            _ = arg1, arg2, o, p

        assert isinstance(cmd.arg1, Arguments) and cmd.arg1.pattern == (str,)
        assert isinstance(cmd.arg2, Arguments) and cmd.arg2.pattern == (int,)
        assert (
            isinstance(cmd.o, Option)
            and cmd.o.type == int
            and cmd.o.long == "--o"
        )
        assert (
            isinstance(cmd.p, Option)
            and cmd.p.type == str
            and cmd.p.long == "--p"
        )

    def test_command_creation(self):
        manually_created_option = self.manually_created_option

        def func(
            pos1: int,  # Arguments(int)
            *pos_any,  # Arguments((str, ...))
            opt1: bool,  # Option("-o", "--opt", argtype=bool)
            opt2: float = 3,  # Option("--opt", argtype=float, default=3)
            opt_3,  # Option("--opt-3", argtype=str)
            opt4: manually_created_option
        ):
            _ = pos1, pos_any, opt1, opt2, opt_3, opt4

        cmd = dryparse.command(func)

        assert isinstance(cmd.pos1, Arguments) and cmd.pos1.pattern == (int,)
        assert isinstance(cmd.pos_any, Arguments) and cmd.pos_any.pattern == (
            (str, ...),
        )
        assert (
            isinstance(cmd.opt1, Option)
            and cmd.opt1.value is None
            and cmd.opt1.type == bool
            and cmd.opt1.long == "--opt1"
            and cmd.opt1.short == "-o"
        )
        assert (
            isinstance(cmd.opt2, Option)
            and cmd.opt2.value == 3
            and cmd.opt2.type == float
            and cmd.opt2.long == "--opt2"
        )
        assert (
            isinstance(cmd.opt_3, Option)
            and cmd.opt_3.value is None
            and cmd.opt_3.type == str
            and cmd.opt_3.long == "--opt-3"
        )
        assert cmd.opt4 is manually_created_option

    def test_help(self):
        @dryparse.command
        def cmd(arg1, *args, opt1=None, opt2="Hello"):
            """A test command.

            Additional description.

            :param arg1: Argument no. 1
            :param args: Remaining arguments
            :param opt1: Option no. 1
            :param opt2: Option no. 2
            """
            _ = arg1, args, opt1, opt2

        meta = Meta(cmd)
        help = meta.help
        assert str(help.desc) == "A test command.\n\nAdditional description."
        assert str(cmd.arg1.help.desc) == "Argument no. 1"
        assert str(cmd.args.help.desc) == "Remaining arguments"
        assert str(cmd.opt1.help.desc) == "Option no. 1"
        assert str(cmd.opt2.help.desc) == "Option no. 2 (default: 'Hello')"
