"""
Test if annex filter rules work properly.
"""
import shutil
from runner import Runner
import util
import pytest
from glob import glob


@pytest.fixture
def runner():
    r = Runner()
    r.login()

    reponame = util.randrepo()
    r.runcommand("gin", "create", reponame,
                 "Test repository for annex filtering")
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame
    r.reponame = reponame

    yield r

    r.cleanup()
    r.logout()


def test_annex_filters(runner):
    r = runner

    # Create some big data files
    for idx in range(3):
        util.mkrandfile(f"randfile{idx}", 1000)

    r.runcommand("gin", "upload", ".")

    def isannexed(fname):
        return util.isannexed(r, fname)

    # annexed files should include path to annex objects in their git blob
    for idx in range(3):
        fname = f"randfile{idx}"
        assert isannexed(fname)

    # Create markdown, python, and 'foo' file
    # All these are extensions that are excluded from annex in the config
    # Make them "large" (bigger than annex threshold)
    excludedfiles = ["markdown.md", "python.py", "biscuits.foo"]
    for fname in excludedfiles:
        util.mkrandfile(fname, 500)

    r.runcommand("gin", "upload", *excludedfiles)
    for fname in excludedfiles:
        assert not isannexed(fname)

    # make a really big "script"
    util.mkrandfile("bigscript.py", 100000)  # 100 MB
    r.runcommand("ls", "-lh")
    r.runcommand("gin", "upload", "bigscript.py")
    assert not isannexed("bigscript.py")

    # clear local directory and reclone
    r.runcommand("gin", "annex", "uninit")
    r.cdrel("..")
    shutil.rmtree(r.reponame)

    repopath = f"{r.username}/{r.reponame}"
    r.runcommand("gin", "get", repopath)
    r.cdrel(r.reponame)

    # git files should be here
    status = util.zerostatus()
    status["OK"] = 4
    status["NC"] = 3
    util.assert_status(r, status=status)

    for fname in glob("randfile*"):
        assert isannexed(fname)

    # download first rand file
    r.runcommand("gin", "get-content", "randfile1")
    status["OK"] += 1
    status["NC"] -= 1
    util.assert_status(r, status=status)

    # download everything
    r.runcommand("gin", "getc", ".")
    status["OK"] += status["NC"]
    status["NC"] = 0
    util.assert_status(r, status=status)
