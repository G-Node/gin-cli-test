import os
from random import randint
from hashlib import md5


def zerostatus():
    return {"OK": 0, "UL": 0, "NC": 0, "MD": 0, "LC": 0, "RM": 0, "??": 0}


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
    n, _ = r.runcommand("git", "rev-list", "--count", "master", echo=False)
    return int(n)


def assert_status(r, path=".", status=dict()):
    """
    Run `gin ls --short` and check the count for each status against the given
    `status` dictionary.
    """
    out, err = r.runcommand("gin", "ls", "--short", path)
    actual = {}
    for code, count in status.items():
        s = sum(1 for line in out.splitlines() if line.startswith(code))
        actual[code] = s
    assert status == actual, (f"Status count mismatch\n"
                              f"Exp: {status}\n"
                              f"Act: {actual}")


def md5sum(filename, printhash=False):
    with open(filename, "rb") as thefile:
        fdata = thefile.read()
        msum = md5(fdata).hexdigest()
    return msum


def hashtree(r):
    curtree = dict()
    head, err = r.runcommand("git", "rev-parse", "HEAD", echo=False)
    print(f"Hashing files in working tree (at {head})")

    gitfiles, err = r.runcommand("git", "ls-files", echo=False)
    gitfiles = gitfiles.splitlines()
    r.runcommand("gin", "get-content", ".", echo=False)
    r.runcommand("gin", "unlock", ".", echo=False)
    for filepath in gitfiles:
        msum = md5sum(filepath)
        curtree[filepath] = msum
        # print(f"{filepath}: {msum}")

    r.runcommand("gin", "lock", ".", echo=False)
    return head, curtree


def lsfiles(path):
    files = []
    for root, dirs, fnames in os.walk(path):
        files.extend([os.path.join(root, f)
                      for f in fnames])
    return files
