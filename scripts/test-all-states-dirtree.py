import os
import shutil
from random import randint
from runner import Runner
import util


zerostatus = {"OK": 0, "UL": 0, "NC": 0, "MD": 0, "LC": 0, "RM": 0, "??": 0}


def test_all_states():
    r = Runner()
    r.login()

    # create repo (remote and local) and cd into directory
    reponame = f"gin-test-{randint(0, 9999):04}"
    r.runcommand("gin", "create", reponame,
                 "Test repository for all states. Created with test scripts")
    r.cdrel(reponame)

    # create files in root
    for idx in range(50):
        util.mkrandfile(f"root-{idx}.git", 5)
    for idx in range(70, 90):
        util.mkrandfile(f"root-{idx}.annex", 2000)

    status = zerostatus.copy()
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

    # modify all tracked files
    r.runcommand("gin", "unlock", ".")
    status["UL"] += 20
    status["OK"] -= 20
    util.assert_status(r, status=status)
    for idx in range(50):
        util.mkrandfile(f"root-{idx}.git", 4)
    for idx in range(70, 90):
        util.mkrandfile(f"root-{idx}.annex", 2100)
    status["OK"] = 0
    status["MD"] = 50
    util.assert_status(r, status=status)

    r.runcommand("gin", "lock", ".")
    status["LC"] += 20
    status["UL"] = 0
    util.assert_status(r, status=status)

    # Upload all except untracked
    r.runcommand("gin", "upload", "*.annex", "*.git")
    status["LC"] = 0
    status["MD"] = 0
    status["OK"] = 70
    util.assert_status(r, status=status)

    # Should have 3 commits so far
    assert util.getrevcount(r) == 3

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
    r.runcommand("gin", "upload", "subdir-a", "subdir-b/subfile-5.annex",
                 "subdir-b/subfile-9.annex")
    status["OK"] += 12
    status["??"] -= 12
    util.assert_status(r, status=status)
    subb = zerostatus.copy()
    subb["OK"] = 2
    subb["??"] = 8
    util.assert_status(r, path="subdir-b", status={"OK": 2, "??": 8})

    tenuntracked = zerostatus.copy()
    tenuntracked["??"] = 10
    for idx in "cdef":
        util.assert_status(r, path=f"subdir-{idx}", status=tenuntracked)

    # Unlock some files
    r.runcommand("gin", "unlock", "root-70.annex",
                 "root-75.annex", "root-84.annex")
    status["UL"] += 3
    status["OK"] -= 3
    util.assert_status(r, status=status)

    # Unlock a whole directory
    r.runcommand("gin", "unlock", "subdir-a")
    status["UL"] += 10
    status["OK"] -= 10
    util.assert_status(r, status=status)

    # Check subdirectory only
    tenul = zerostatus.copy()
    tenul["UL"] = 10
    util.assert_status(r, path="subdir-a", status=tenul)

    # Check again from within the subdir
    r.cdrel("subdir-a")
    util.assert_status(r, status=tenul)
    r.cdrel("..")

    # Relock one of the files
    r.runcommand("gin", "lock", "root-84.annex")
    status["UL"] -= 1
    status["OK"] += 1
    util.assert_status(r, status=status)

    oneul = zerostatus.copy()
    oneul["UL"] = 1
    # Check one of the remaining unlocked files explicitly
    util.assert_status(r, status=oneul, path="root-70.annex")

    # There should be no NC files so far
    status["NC"] = 0
    util.assert_status(r, status=status)

    # Drop some files
    r.runcommand("gin", "rmc", "subdir-b/subfile-5.annex")
    status["NC"] += 1
    status["OK"] -= 1
    util.assert_status(r, status=status)

    # change subdir-a from 'unlocked' to 'no content'
    r.runcommand("gin", "remove-content", "subdir-a")
    status["NC"] += 10
    status["UL"] -= 10
    util.assert_status(r, status=status)

    suba = zerostatus.copy()
    suba["NC"] += 10
    util.assert_status(r, status=suba, path="subdir-a")
    subb["OK"] -= 1
    subb["NC"] += 1
    util.assert_status(r, status=subb, path="subdir-b")

    # Upload everything and then rmc it
    r.runcommand("gin", "upload", ".")
    status["OK"] += status["UL"] + status["MD"] + status["LC"] + status["??"]
    status["UL"] = status["MD"] = status["LC"] = status["??"] = 0
    util.assert_status(r, status=status)

    r.runcommand("gin", "rmc", ".")
    # annex files are now NC
    status["NC"] += 69
    status["OK"] -= 69
    util.assert_status(r, status=status)

    # remove a few file and check their status
    os.remove("subdir-a/subfile-1.annex")
    os.remove("root-10.git")
    shutil.rmtree("subdir-b")
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
    shutil.rmtree("subdir-c")
    status["RM"] += 10
    status["??"] += 2
    status["NC"] -= 10
    util.assert_status(r, status=status)

    r.runcommand("gin", "upload", ".")
    status["RM"] = 0
    status["OK"] += status["??"]
    status["??"] = 0
    util.assert_status(r, status=status)

    r.cleanup(reponame)
    r.logout()

    print("DONE!")
