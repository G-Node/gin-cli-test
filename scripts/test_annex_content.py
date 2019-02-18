"""
Tests for an issue that can occur in direct mode where the target of a symlink
can become the contents of the blob itself.

The same test is run in indirect mode, even though it's not likely to occur
there.
"""
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()
    r.login()

    reponame = util.randrepo()
    r.runcommand("gin", "create", reponame,
                 "Test repository for all states")
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


def test_annex_content_indirect(runner):
    run_checks(runner, mode=1)
    print("Done!")


def test_annex_content_direct(runner):
    print("************ SWITCHING TO DIRECT MODE ************")
    runner.runcommand("git", "annex", "direct")
    run_checks(runner, mode=0)
    print("Done!")


def run_checks(r, mode):
    # create files in root
    for idx in range(10, 15):
        util.mkrandfile(f"root-{idx}.git", 5)
    for idx in range(20, 24):
        util.mkrandfile(f"root-{idx}.annex", 2000)

    r.runcommand("gin", "commit", "root*")

    # check that all annexed files are symlinks (in git)
    out, err = r.runcommand("git", "ls-files", "-s")
    assert not err
    outlines = out.splitlines()
    for line in outlines:
        line = line.strip()
        if line.endswith(".annex"):
            assert line[:6] == "120000"
        elif line.endswith(".git"):
            assert line[:3] == "100"
        else:
            assert False, "Found unexpected file in repository"

    # check if the size of each annexed file in git is less than 500 bytes
    for idx in range(20, 24):
        fname = f"root-{idx}.annex"
        out, err = r.runcommand("git", "cat-file", "-s", f":{fname}")
        assert not err
        assert int(out) < 500

        out, err = r.runcommand("git", "cat-file", "-p", f":{fname}")
        assert not err
        assert "annex" in out
        assert "MD5-" in out
