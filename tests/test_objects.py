import pytest

from dryparse.objects import Arguments
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
        assert args.convert(["test"]) == "test"
        args = Arguments((str, 1))
        assert args.convert(["test"]) == "test"
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
