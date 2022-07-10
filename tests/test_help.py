import copy

import pytest

import lib
from dryparse.help import HelpSectionList, HelpSection, Description
from dryparse.objects import Meta


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
    def test(self):
        pass


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
