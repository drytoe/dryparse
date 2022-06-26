import textwrap

from dryparse import Command, parse
from dryparse.objects import Option, RootCommand, Arguments
from dryparse.parser import parse_arg


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
        cmd.output = Option("-o", "--output", type=str)
        opt, value = parse_arg(cmd, "-ofile1")
        assert isinstance(opt, Option) and value == "file1"
        opt, value = parse_arg(cmd, "--output=file2")
        assert isinstance(opt, Option) and value == "file2"

    def test_parse_command_with_options(self):
        cmd = Command("test")
        cmd.random = Option("-r", "--random")
        cmd.output = Option("-o", "--output", type=str)
        args = [
            "test",
            "-r",
            "--output",
            "file",
        ]

        cmd = parse(cmd, args)
        assert type(cmd.random) == bool and cmd.random and cmd.output == "file"

    def test_parse_command_help(self, capfd):
        cmd = Command("test")
        random = Option("-r", "--random")
        cmd.random = random
        random.help.signature = "--random, -r"
        cmd.output = Option("-o", "--output", type=str, desc="output file")
        cmd.config = Option(long="--config", type=str, argname="FILE")
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
        cmd = Command("test")
        cmd.opt1 = Option("-1", "--opt1", default="opt1_default")
        cmd.opt2 = Option("-2", "--opt2", default="opt2_default", type=int)
        cmd.args = Arguments([bool, int])

        cmd = parse(cmd, ["test", "--opt2", "opt2_value", "True", "10"])


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
        run.interactive = Option(
            "-i", "--interactive", desc="Keep STDIN open even if not attached"
        )
        run.tty = Option("-t", "--tty", desc="TODO")

    def test_help(self, capfd):
        cmd = parse(self.cmd, ["/usr/bin/docker", "-D", "run", "TODO"])
