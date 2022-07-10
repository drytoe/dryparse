import copy

import pytest

import lib
from dryparse.help import HelpSectionList, HelpSection, Description
from dryparse.objects import Meta, Arguments, Command


class TestHelp:
    def test_deepcopy(self):
        git = lib.create_git_command()
        h = Meta(git).help
        h.desc = "testson"
        h.signature = "signature"
        h.sections = HelpSectionList()
        h.sections.usage = HelpSection("Usage")
        h.sections.usage.headline = "Usage:"
        h.sections.usage.indent = 4
        h1 = copy.deepcopy(h)
        # TODO


class TestArgumentsHelp:
    def test_single(self):
        a = Arguments(str, desc="a single arg")
        cmd = Command("cmd")
        cmd.arg = a
        h = a.help
        # Name auto assignment
        assert h.name == "arg"
        assert h.desc == "a single arg"
        assert h.signature == "arg"
        assert h.hint == h.signature

    def test_signature_2(self):
        assert (
            Arguments((str, 1), (int, 2), bool, name="arg").help.signature
            == "arg{4}"
        )

    def test_signature_0_or_more(self):
        assert Arguments((str, ...), name="arg").help.signature == "[arg...]"

    def test_signature_1_or_more(self):
        assert (
            Arguments(int, (str, ...), name="arg").help.signature
            == "arg{1...}"
        )

    def test_signature_0_to_2(self):
        assert (
            Arguments((int, range(0, 2)), name="arg").help.signature
            == "[arg{0..2}]"
        )

    def test_signature_1_to_3(self):
        assert (
            Arguments((int, range(1, 3)), name="arg").help.signature
            == "arg{1..3}"
        )


class TestHelperObjects:
    def test_description(self):
        desc = Description("long")
        assert desc.long == "long"
        assert desc.brief == "long"

        desc = Description("long", "brief")
        assert desc.long == "long"
        assert desc.brief == "brief"

        _desc = Description("long", "brief")
        desc = Description(_desc)
        assert desc.long == "long"
        assert desc.brief == "brief"

        with pytest.raises(ValueError):
            _desc = Description(_desc, brief="asdfasdf")
