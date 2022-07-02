import dryparse
from dryparse.objects import Option, Arguments, Meta


def create_cp_command():
    @dryparse.command
    def cp(source: str, dest: str, *, recursive=False):
        pass

    return cp


class TestCommandDecorator:
    manually_created_option: Option = None

    @classmethod
    def setup_class(cls):
        cls.manually_created_option = Option("-O", "--Opt4")

    def test_command_creation(self):
        manually_created_option = self.manually_created_option

        def func(
            pos1: int,  # Arguments(int)
            *pos_any: str,  # Arguments((str, ...))
            opt1: bool,  # Option("-o", "--opt1", argtype=bool)
            opt2: float = 3,  # Option("--opt1", argtype=float, default=3)
            opt_3,  # Option("--opt-3", argtype=str)
            opt4: manually_created_option
        ):
            pass

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

    def test_parsing(self):
        manually_created_option = self.manually_created_option
        callback_called = False

        @dryparse.command
        def cmd(
            pos1: int,  # Arguments(int)
            *pos_any: str,  # Arguments((str, ...))
            opt1: bool,  # Option("-o", "--opt1", argtype=bool)
            opt2: float = 3,  # Option("--opt1", argtype=float, default=3)
            opt_3,  # Option("--opt-3", argtype=str)
            opt4: manually_created_option
        ):
            nonlocal callback_called
            callback_called = True
            assert pos1 == 1
            assert list(pos_any) == ["a", "b"]
            assert opt1 is True
            assert opt2 == 4
            assert opt_3 == "opt3_value"
            assert opt4 is True

        cmd = dryparse.parse(
            cmd,
            [
                "cmd",
                "1",
                "a",
                "b",
                "--opt1",
                "--opt2=4",
                "--opt-3",
                "opt3_value",
                "--Opt4",
            ],
        )
        cmd()
        assert callback_called

    def test_help(self):
        pass
