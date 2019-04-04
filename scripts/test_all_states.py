"""
Runs through all possible file states and checks the output of 'gin ls'.
"""
import os
import shutil
import tempfile
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner(True)
    r.login()

    reponame = util.randrepo()
    r.runcommand("gin", "create", reponame,
                 "Test repository for all states")
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


@pytest.fixture
def orunner():
    remoteloc = tempfile.TemporaryDirectory(prefix="gintest-remote")
    r = Runner(False)
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


@pytest.mark.slow
def test_all_states(runner):
    run_checks(runner)
    print("Done!")


@pytest.mark.offline
@pytest.mark.slow
def test_all_states_offline(orunner):
    print("Using directory remote")
    run_checks(orunner)


def run_checks(r):
    # create files in root
    for idx in range(50):
        util.mkrandfile(f"root-{idx}.git", 5)
    for idx in range(70, 90):
        util.mkrandfile(f"root-{idx}.annex", 2000)

    status = util.zerostatus()
    status["??"] += 70
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", "root*")
    status["LC"] += 70
    status["??"] -= 70
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload")
    status["LC"] -= 70
    status["OK"] += 70
    util.assert_status(r, status=status)

    # gin upload command should not have created an extra commit
    assert util.getrevcount(r) == 2

    # Create more root files that will remain UNTRACKED
    for idx in "abcdef":
        util.mkrandfile(f"root-file-{idx}.untracked", 1)
    status["??"] += 6
    util.assert_status(r, status=status)

    # lock all annexed files
    r.runcommand("gin", "lock", ".")
    status["TC"] += 20
    status["OK"] -= 20
    util.assert_status(r, status=status)

    # commit typechange
    r.runcommand("gin", "commit")
    status["TC"] -= 20
    status["OK"] += 20
    util.assert_status(r, status=status)

    # modify all tracked files
    r.runcommand("gin", "unlock", ".")
    status["TC"] += 20
    status["OK"] -= 20
    util.assert_status(r, status=status)
    for idx in range(50):
        util.mkrandfile(f"root-{idx}.git", 4)
    for idx in range(70, 90):
        util.mkrandfile(f"root-{idx}.annex", 2100)
    status["OK"] = 0
    status["TC"] = 0
    status["MD"] = 70
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", "*.git", "*.annex")
    status["LC"] += status["MD"]
    status["MD"] = 0
    util.assert_status(r, status=status)

    # Upload all except untracked
    r.runcommand("gin", "upload", "*.annex", "*.git")
    status["LC"] = 0
    status["MD"] = 0
    status["OK"] = 70
    util.assert_status(r, status=status)

    # Should have 4 commits so far
    assert util.getrevcount(r) == 4

    # Create some subdirectories with files
    for idx in "abcdef":
        dirname = f"subdir-{idx}"
        os.mkdir(dirname)
        r.cdrel(dirname)
        for jdx in range(10):
            util.mkrandfile(f"subfile-{jdx}.annex", 1500)
        r.cdrel("..")
    status["??"] += 60
    util.assert_status(r, status=status)

    # Upload the files in the first subdirectory only and a couple from the
    # second
    r.runcommand("gin", "upload", "subdir-a",
                 os.path.join("subdir-b", "subfile-5.annex"),
                 os.path.join("subdir-b", "subfile-9.annex"))
    status["OK"] += 12
    status["??"] -= 12
    util.assert_status(r, status=status)
    subb = util.zerostatus()
    subb["OK"] = 2
    subb["??"] = 8
    util.assert_status(r, path="subdir-b", status=subb)

    tenuntracked = util.zerostatus()
    tenuntracked["??"] = 10
    for idx in "cdef":
        util.assert_status(r, path=f"subdir-{idx}", status=tenuntracked)

    # Lock some files
    r.runcommand("gin", "lock", "root-70.annex", "root-75.annex",
                 "root-84.annex")
    status["TC"] += 3
    status["OK"] -= 3
    util.assert_status(r, status=status)

    # Lock a whole directory
    r.runcommand("gin", "lock", "subdir-a")
    status["TC"] += 10
    status["OK"] -= 10
    util.assert_status(r, status=status)

    # Check subdirectory only
    tenul = util.zerostatus()
    tenul["TC"] = 10
    util.assert_status(r, path="subdir-a", status=tenul)

    # Check again from within the subdir
    r.cdrel("subdir-a")
    util.assert_status(r, status=tenul)
    r.cdrel("..")

    # Revert lock on one of the files
    r.runcommand("gin", "unlock", "root-84.annex")
    status["TC"] -= 1
    status["OK"] += 1
    util.assert_status(r, status=status)

    onetc = util.zerostatus()
    onetc["TC"] = 1

    # Check one of the remaining locked files explicitly
    util.assert_status(r, status=onetc, path="root-70.annex")

    # There should be no NC files so far
    status["NC"] = 0
    util.assert_status(r, status=status)

    # Drop some files
    r.runcommand("gin", "rmc", os.path.join("subdir-b", "subfile-5.annex"))
    status["NC"] += 1
    status["OK"] -= 1
    util.assert_status(r, status=status)

    # remove content in subdir-a
    r.runcommand("gin", "remove-content", "subdir-a")
    # removing content of TypeChanged files still shows them as unlocked until
    # the type change is committed
    util.assert_status(r, status=status)

    suba = util.zerostatus()
    suba["TC"] += 10
    util.assert_status(r, status=suba, path="subdir-a")
    subb["OK"] -= 1
    subb["NC"] += 1
    util.assert_status(r, status=subb, path="subdir-b")

    # Upload everything and then rmc it
    r.runcommand("gin", "upload", ".")
    # subdir-a goes from TC to NC (unlocked, removed content, then commit)
    status["TC"] -= 10
    status["NC"] += 10
    # modified and untracked files become OK
    status["OK"] += status["TC"] + status["MD"] + status["LC"] + status["??"]
    # everything else becomes 0
    status["TC"] = status["MD"] = status["LC"] = status["??"] = 0
    util.assert_status(r, status=status)

    r.runcommand("gin", "rmc", ".")
    # annex files are now NC
    status["NC"] += 69
    status["OK"] -= 69
    util.assert_status(r, status=status)

    # remove a few files and check their status
    os.remove(os.path.join("subdir-a", "subfile-1.annex"))
    os.remove("root-10.git")
    shutil.rmtree("subdir-b", onerror=util.force_rm)
    status["RM"] += 12
    status["NC"] -= 11
    status["OK"] -= 1
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", ".")
    status["RM"] = 0
    util.assert_status(r, status=status)

    # Add new files, remove some existing ones, check status and upload
    util.mkrandfile("new-annex-file", 10021)
    util.mkrandfile("new-git-file", 10)
    shutil.rmtree("subdir-c", onerror=util.force_rm)
    status["RM"] += 10
    status["??"] += 2
    status["NC"] -= 10
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload", ".")
    status["RM"] = 0
    status["OK"] += status["??"]
    status["??"] = 0
    util.assert_status(r, status=status)
