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
