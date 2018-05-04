import os
from random import randint


def randrepo():
    return f"gin-test-{randint(0, 9999):04}"


def mkrandfile(name, size=100):
    """
    Make a random binary file with a given name and size in kilobytes
    (default: 100k)
    """
    with open(name, "wb") as f:
        f.write(os.urandom(size*1024))


def getrevcount(r):
    """
    Total number of revisions from HEAD.
    """
    n, _ = r.runcommand("git", "rev-list", "--count", "HEAD",
                               echo=False)
    return int(n)


def assert_status(r, path=".", status=dict()):
    """
    Run `gin ls --short` and check the count for each status against the given
    `status` dictionary.
    """
    out, err = r.runcommand("gin", "ls", "--short", path)
    for code, count in status.items():
        s = sum(1 for line in out.splitlines() if line.startswith(code))
        assert s == count, f"[{code}] Expected {count}, got {s}"
