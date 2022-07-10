import copy

import pytest

import lib
from dryparse.help import HelpSectionList, HelpSection, CommandDescription
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
    def test_command_description(self):
        desc = CommandDescription("long")
        assert desc.long == "long"
        assert desc.brief == "long"

        desc = CommandDescription("long", "brief")
        assert desc.long == "long"
        assert desc.brief == "brief"

        _desc = CommandDescription("long", "brief")
        desc = CommandDescription(_desc)
        assert desc.long == "long"
        assert desc.brief == "brief"

        with pytest.raises(ValueError):
            _desc = CommandDescription(_desc, brief="asdfasdf")
