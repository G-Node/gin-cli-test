"""
 1. Create a test repository
 2. Create files
 3. Compute hashes for the new files
 4. Upload the files
 5. Delete the local copy of the repository
 6. Clone the repository
 8. Check that the annexed files are placeholders and have no content
 9. Check that the git files have the correct hashes
 9. Download the first file and check that only one file has content and
 correct md5 hash
10. Download the second file and check that both files have content and
correct md5 hashes
11. Delete the local copy of the repository
"""
import os
import tempfile
import shutil
from glob import glob
from runner import Runner
import util
import pytest


def hashfiles():
    hashes = dict()
    for fname in glob("*"):
        if os.path.exists(fname):
            hashes[fname] = util.md5sum(fname)
        else:
            # For broken links: annexed files without content
            hashes[fname] = None
    return hashes


@pytest.fixture
def runner():
    r = Runner()
    r.login()

    reponame = util.randrepo()
    r.runcommand("gin", "create", reponame,
                 "Test a minimal workflow")
    r.reponame = reponame
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


@pytest.fixture
def drunner():
    remoteloc = tempfile.TemporaryDirectory(prefix="gin-cli-test")
    r = Runner()

    reponame = util.randrepo()
    r.reponame = reponame
    os.mkdir(reponame)
    r.cdrel(reponame)

    # Create repo in A
    r.runcommand("gin", "init")
    r.runcommand("gin", "add-remote", "--create", "--default",
                 "origin", f"dir:{remoteloc.name}")
    r.runcommand("gin", "upload")
    r.repositories[r.cmdloc] = None
    r.remotedir = remoteloc

    yield r

    r.cleanup()


def test_workflow(runner):
    r = runner

    # create files in root
    for idx in range(5):
        util.mkrandfile(f"root-{idx}.git", 5)
    for idx in range(7):
        util.mkrandfile(f"root-{idx}.annex", 2000)

    # compute hashes
    orighashes = hashfiles()
    print(orighashes)

    # upload
    r.runcommand("gin", "upload", ".")

    # cleanup local repository
    r.runcommand("gin", "annex", "uninit")
    r.cdrel("..")
    shutil.rmtree(r.reponame, onerror=util.force_rm)

    # redownload and check the hashes
    repopath = f"{r.username}/{r.reponame}"
    r.runcommand("gin", "get", repopath)
    r.cdrel(r.reponame)

    # should have 5 OK files and 7 NC files
    status = util.zerostatus()
    status["OK"] = 5
    status["NC"] = 7
    util.assert_status(r, status=status)

    curhashes = hashfiles()
    for k in curhashes:
        orig = orighashes[k]
        cur = curhashes[k]
        if k.endswith("git"):
            assert orig == cur
            assert not util.isannexed(r, k)
        elif k.endswith("annex"):
            assert orig != cur
            assert util.isannexed(r, k)
        else:
            assert False, f"Unexpected file {k}"

    r.runcommand("gin", "get-content", "root-1.annex")
    status["OK"] += 1
    status["NC"] -= 1
    util.assert_status(r, status=status)

    curhashes = hashfiles()
    assert orighashes["root-1.annex"] == curhashes["root-1.annex"]
    assert util.isannexed(r, "root-1.annex")

    # download everything
    r.runcommand("gin", "getc", ".")

    # everything should be OK
    status["OK"] += status["NC"]
    status["NC"] = 0
    util.assert_status(r, status=status)

    # all hashes should match original now
    curhashes = hashfiles()
    assert curhashes == orighashes


def test_workflow_directory(drunner):
    r = drunner

    # create files in root
    for idx in range(5):
        util.mkrandfile(f"root-{idx}.git", 5)
    for idx in range(7):
        util.mkrandfile(f"root-{idx}.annex", 2000)

    # compute hashes
    orighashes = hashfiles()
    print(orighashes)

    # upload
    r.runcommand("gin", "upload", ".")

    # cleanup local repository
    r.runcommand("gin", "annex", "uninit")
    r.cdrel("..")
    shutil.rmtree(r.reponame, onerror=util.force_rm)

    # redownload and check the hashes
    os.mkdir(r.reponame)
    r.cdrel(r.reponame)
    r.runcommand("gin", "init")
    r.runcommand("gin", "add-remote", "--default",
                 "origin", f"dir:{r.remotedir.name}")
    r.runcommand("gin", "download")

    # should have 5 OK files and 7 NC files
    status = util.zerostatus()
    status["OK"] = 5
    status["NC"] = 7
    util.assert_status(r, status=status)

    curhashes = hashfiles()
    for k in curhashes:
        orig = orighashes[k]
        cur = curhashes[k]
        if k.endswith("git"):
            assert orig == cur
            assert not util.isannexed(r, k)
        elif k.endswith("annex"):
            assert orig != cur
            assert util.isannexed(r, k)
        else:
            assert False, f"Unexpected file {k}"

    r.runcommand("gin", "get-content", "root-1.annex")
    status["OK"] += 1
    status["NC"] -= 1
    util.assert_status(r, status=status)

    curhashes = hashfiles()
    assert orighashes["root-1.annex"] == curhashes["root-1.annex"]
    assert util.isannexed(r, k)

    # download everything
    r.runcommand("gin", "getc", ".")

    # everything should be OK
    status["OK"] += status["NC"]
    status["NC"] = 0
    util.assert_status(r, status=status)

    # all hashes should match original now
    curhashes = hashfiles()
    assert curhashes == orighashes
