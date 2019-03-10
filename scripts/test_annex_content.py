"""
Tests for an issue that can occur in direct mode where the target of a symlink
can become the contents of the blob itself.

The same test is run in indirect mode, even though it's not likely to occur
there.
"""
import os
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()

    reponame = util.randrepo()
    os.mkdir(reponame)
    r.cdrel(reponame)

    r.runcommand("gin", "init")
    r.repositories[r.cmdloc] = reponame

    yield r

    r.runcommand("gin", "annex", "uninit")


def test_annex_content_indirect(runner):
    run_checks(runner, mode=1)
    print("Done!")


@pytest.mark.skip("Direct mode not supported")
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

    def check_files():
        # check if the size of each file is < 10k
        # git files are 5k, annexed files are 2000k
        # pointer files should be a few bytes
        out, err = r.runcommand("git", "ls-files")
        allfiles = out.splitlines()
        for fname in allfiles:
            out, err = r.runcommand("git", "cat-file", "-s", f":{fname}")
            assert not err
            assert int(out) < 10240

            if fname.endswith(".annex"):
                out, err = r.runcommand("git", "cat-file", "-p", f":{fname}")
                assert not err
                assert "annex" in out
                assert "MD5-" in out

    check_files()

    # create files in subdirectories
    os.mkdir("subdir-a")
    r.cdrel("subdir-a")
    for idx in range(10, 13):
        util.mkrandfile(f"a-{idx}.git", 5)
    for idx in range(20, 23):
        util.mkrandfile(f"a-{idx}.annex", 2000)

    # commit from inside
    r.runcommand("gin", "commit", ".")
    r.cdrel("..")
    check_files()

    os.mkdir("subdir-b")
    r.cdrel("subdir-b")
    for idx in range(10, 13):
        util.mkrandfile(f"b-{idx}.git", 5)
    for idx in range(20, 23):
        util.mkrandfile(f"b-{idx}.annex", 2000)

    r.cdrel("..")
    # commit from outside
    r.runcommand("gin", "commit", "subdir-b")
    check_files()
