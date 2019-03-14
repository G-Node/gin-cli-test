"""
Tests remove and commit
"""
import os
import tempfile
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    remoteloc = tempfile.TemporaryDirectory(prefix="gintest-remote")
    r = Runner()
    reponame = util.randrepo()
    os.mkdir(reponame)
    r.cdrel(reponame)
    r.runcommand("gin", "init")
    r.runcommand("gin", "add-remote", "--create", "--default",
                 "origin", f"dir:{remoteloc.name}")
    r.runcommand("gin", "upload")

    r.repositories[r.cmdloc] = None

    yield r

    r.cleanup()


def test_rm_commit_directory(runner):
    r = runner
    # create files in root
    for idx in range(6):
        util.mkrandfile(f"root-{idx}.git", 5)
        util.mkrandfile(f"root-{idx}.annex", 2000)

    status = util.zerostatus()
    status["??"] += 12
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", "root*")
    status["LC"] += 12
    status["??"] -= 12
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload")
    status["LC"] -= 12
    status["OK"] += 12
    util.assert_status(r, status=status)

    for idx in range(2, 4):
        os.remove(f"root-{idx}.git")
        os.remove(f"root-{idx}.annex")
    status["OK"] -= 4
    status["RM"] += 4
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload", ".")
    status["RM"] = 0
    util.assert_status(r, status=status)
