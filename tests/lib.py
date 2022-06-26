from dryparse import Command
from dryparse.objects import RootCommand, Option, Arguments


def create_git_command():
    git = RootCommand("git", "A VCS software")
    git.commit = Command("commit", "Commit changes")
    git.commit.message = Option("-m", "--message", desc="commit message")
    git.add = Command("add", "Add files")
    git.add.pathspecs = Arguments([(str, ...)])
    git.add.update = Option("-u", "--update", desc="update tracked files")
    return git
