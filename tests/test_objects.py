import copy

import pytest

from dryparse.objects import Arguments, Command, Meta, Option
from dryparse.errors import (
    InvalidArgumentPatternError,
    ArgumentConversionError,
)

from dryparse.errors import PatternAfterFlexiblePatternError


class TestArguments:
    def test_valid_constructors(self):
        Arguments()
        Arguments(int)
        Arguments(int, str)
        Arguments(int, (str, 2))
        Arguments((int, 2), (str, 3))
        Arguments((int, range(1, 3)))
        Arguments((int, ...))
        Arguments(bool, str, (int, ...))

    def test_invalid_constructors(self):
        with pytest.raises(InvalidArgumentPatternError):
            Arguments(1)  # Dead wrong type
        with pytest.raises(InvalidArgumentPatternError):
            Arguments(int, (int,))  # Wrong tuple length
        with pytest.raises(InvalidArgumentPatternError):
            Arguments(int, (1, 1))  # Invalid tuple type
        with pytest.raises(InvalidArgumentPatternError):
            Arguments(int, (int, True))  # Invalid tuple type
        with pytest.raises(PatternAfterFlexiblePatternError):
            Arguments(int, (str, ...), int)  # Pattern after (type, ...)
        with pytest.raises(PatternAfterFlexiblePatternError):
            Arguments(
                int, (str, range(2, 3)), int
            )  # Pattern after (type, range)
        with pytest.raises(PatternAfterFlexiblePatternError):
            Arguments(int, (str, range(2, 3)), (int, ...))  # Combination
        with pytest.raises(PatternAfterFlexiblePatternError):
            Arguments(int, (int, ...), (str, range(2, 3)))  # Combination

    def test_convert(self):
        args = Arguments(str)
        assert args.convert(["test"]) == ["test"]
        args = Arguments((str, 1))
        assert args.convert(["test"]) == ["test"]
        args = Arguments(str, int)
        assert args.convert(["test", "1"]) == ["test", 1]
        args = Arguments((int, 2))
        assert args.convert(["1", "2"]) == [1, 2]
        args = Arguments((int, 2), (float, 2))
        assert args.convert(["1", "2", "0.1", "0.2"]) == [1, 2, 0.1, 0.2]
        args = Arguments(bool, (int, 2))
        assert args.convert(["true", "1", "2"]) == [True, 1, 2]
        args = Arguments(str, (int, ...))
        assert args.convert(["test", "1", "2", "3"]) == ["test", 1, 2, 3]
        args = Arguments(str, (int, range(0, 2)))
        assert args.convert(["a"]) == ["a"]
        assert args.convert(["a", "1"]) == ["a", 1]
        assert args.convert(["a", "1", "2"]) == ["a", 1, 2]
        args = Arguments()
        assert args.convert(["a", "b", "c"]) == ["a", "b", "c"]

    def test_convert_errors(self):
        for pattern in (str, (str, 1)):
            args = Arguments(pattern)
            with pytest.raises(ArgumentConversionError):
                args.convert([])
            with pytest.raises(ArgumentConversionError):
                args.convert(["a", "b"])

        args = Arguments((str, 2))
        with pytest.raises(ArgumentConversionError):
            args.convert(["a"])
        with pytest.raises(ArgumentConversionError):
            args.convert(["a", "b", "c"])

        args = Arguments(int)
        with pytest.raises(ArgumentConversionError):
            args.convert(["1", "2"])

        with pytest.raises(ArgumentConversionError):
            args.convert(["non_int"])

        args = Arguments(int, float)
        with pytest.raises(ArgumentConversionError):
            args.convert(["0.1", "1"])

        args = Arguments(int, (float, ...))
        with pytest.raises(ArgumentConversionError):
            args.convert([])

        args = Arguments((int, ...))
        with pytest.raises(ArgumentConversionError):
            args.convert(["test"])
        with pytest.raises(ArgumentConversionError):
            args.convert(["1", "test"])

        args = Arguments((str, range(2, 3)))
        with pytest.raises(ArgumentConversionError):
            args.convert(["a"])
        with pytest.raises(ArgumentConversionError):
            args.convert(["a", "b", "c", "d"])


class TestCommand:
    cmd: Command
    meta: Meta

    @classmethod
    def setup_class(cls):
        cls.cmd = Command("test", regex="^test$", desc="Test command")
        cls.meta = Meta(cls.cmd)

    def test_basic(self):
        assert isinstance(self.cmd.help, Option) and self.cmd.help.type == bool

    def test_meta_instantiation(self):
        assert Meta(self.cmd) == Meta(self.cmd)

    def test_meta_updating(self):
        """Test if Meta(cmd) is properly updated as cmd gets new attributes."""
        assert list(self.meta.options.keys()) == ["help"]
        self.cmd.opt = opt = Option("-o")
        self.cmd.arg = arg = Arguments()
        self.cmd.sub = sub = Command("sub")
        assert (
            self.meta.options.get("opt", None) is opt
            and self.meta.argument_aliases.get("arg", None) is arg
            and self.meta.subcommands.get("sub", None) is sub
        )

        self.cmd.opt2 = Option("-o2")
        self.cmd.arg2 = Arguments()
        self.cmd.sub2 = Command("sub2")
        del self.cmd.opt
        del self.cmd.arg
        del self.cmd.sub
        assert (
            set(self.meta.options.keys()) == {"help", "opt2"}
            and set(self.meta.argument_aliases.keys()) == {"arg2"}
            and set(self.meta.subcommands.keys()) == {"sub2"}
        )

    def test_deepcopy(self):
        cmd = copy.deepcopy(self.cmd)
        cmd.sub = Command("sub")
        meta = Meta(cmd)
        assert self.meta.help is not meta.help
        self.cmd.help.value = True
        assert cmd.help.value != self.cmd.help.value
        self.cmd.help.value = False
        cmd.help.value = True
        assert cmd.help.value != self.cmd.help.value
        assert (
            meta.options is not self.meta.options
            and meta.subcommands is not self.meta.subcommands
            and meta.argument_aliases is not self.meta.argument_aliases
        )
