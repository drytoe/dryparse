from typing import Type

import dryparse
from dryparse import Command
from dryparse.help import CommandHelp, Help
from dryparse.objects import Meta, Option, RootCommand

cmd = Command(name="cmd", desc="A sample command")
opt = Option(long="--long")

if __name__ == "__main__":
    gh = RootCommand("gh", desc="GitHub CLI")
    gh.repo = Command("repo", desc="Repository operations")
    gh.repo.create = Command("create", desc="Create repositories")
    gh.repo.create.homepage = Option(long="--homepage")
    gh.repo.clone = Command("clone", desc="Clone a repository")
    opt = Option(long="--hello")
    chelp = Help(gh)
    assert isinstance(chelp, CommandHelp)
    ohelp = Help(opt)
    ohelp.signature = "-a, --auto AUTO"
    ohelp.desc = "an option"

    @Meta(gh).callback
    def gh_callback():
        print("gh called", Meta(gh).called)

    dryparse.parse(gh)
