import dryparse
from dryparse import Command
from dryparse.objects import Meta

cmd = Command(name="cmd", desc="A sample command")
Meta(cmd)

if __name__ == "__main__":
    pass
    # dryparse.parse(cmd)
