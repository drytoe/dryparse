import copy

import lib
from dryparse.help import HelpSectionList, HelpSection
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
