"""
Initialise repository as v5 then upgrade to v7
"""
import os
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner(True)
    r.login()

    # manually set up repository with annex v5

    reponame = util.randrepo()
    r.runcommand("gin", "create", "--no-clone", reponame,
                 "Test repository for annex upgrade")
    os.mkdir(reponame)
    r.cdrel(reponame)
    r.runcommand("git", "init")
    r.runcommand("git", "annex", "init", "--version=5")
    r.runcommand("gin", "add-remote", "origin",
                 f"test:{r.username}/{reponame}")
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


@pytest.mark.slow
def test_annex_upgrade(runner):
    r = runner

    # checks if all files with suffix ".annex" are annexed files
    def assert_all_annex():
        for root, dirs, files in os.walk("."):
            if ".git" in dirs:
                dirs.remove(".git")  # don't visit .git directory
            for f in files:
                if f.endswith("annex"):
                    fname = os.path.join(root, f)
                    assert util.isannexed(r, fname)

    # add some file, commit, upload, then upgrade
    os.mkdir("first batch")
    fbfiles = 0
    for idx in range(5):
        fname = os.path.join("first batch", f"small-{idx}.git")
        util.mkrandfile(fname, 5)
        fbfiles += 1
    for idx in range(7, 9):
        fname = os.path.join("first batch", f"big-{idx}.annex")
        util.mkrandfile(fname, 2000)
        fbfiles += 1

    status = util.zerostatus()

    status["??"] += fbfiles
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", "first batch")
    status["LC"] += status["??"]
    status["??"] = 0
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)
    assert_all_annex()

    with open(os.path.join(".git", "config")) as gitconf:
        assert "version = 5" in gitconf.read()

    r.runcommand("gin", "annex", "upgrade")
    r.runcommand("gin", "init")
    util.assert_status(r, status=status)

    with open(os.path.join(".git", "config")) as gitconf:
        conf = gitconf.read()
        assert "version = 7" in conf
        assert "addunlocked" in conf
    assert_all_annex()

    os.mkdir("second batch")
    sbfiles = 0
    for idx in range(20, 30):
        fname = os.path.join("second batch", f"small-{idx}.git")
        util.mkrandfile(fname, 5)
        sbfiles += 1
    for idx in range(10, 15):
        fname = os.path.join("second batch", f"big-{idx}.annex")
        util.mkrandfile(fname, 2000)
        sbfiles += 1

    status["??"] += sbfiles

    util.assert_status(r, status=status)
    r.runcommand("gin", "commit", ".")
    status["LC"] += status["??"]
    status["??"] = 0
    util.assert_status(r, status=status)
    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)

    assert_all_annex()
