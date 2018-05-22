import os
import shutil
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()
    # create repo locally only
    reponame = util.randrepo()
    localdir = f"{reponame}"
    os.mkdir(localdir)
    r.cdrel(localdir)
    r.reponame = reponame

    yield r

    print(f"Cleaning up {reponame}")
    # cleanup
    r.cleanup(reponame)
    r.logout()


def test_local_only(runner):
    r = runner

    # redefine cleanup and logout since they would error out
    def cleanup(reponame):
        r.runcommand("gin", "annex", "uninit", exit=False)
    r.cleanup = cleanup

    r.runcommand("gin", "init")

    ngit = 15
    nannex = 10
    nuntracked = 5

    # create files in root
    for idx in range(ngit):
        util.mkrandfile(f"root-{idx}.git", 1)
    for idx in range(nannex):
        util.mkrandfile(f"root-{idx}.annex", 100)

    status = util.zerostatus()
    status["??"] = nannex + ngit
    util.assert_status(r, status=status)

    out, err = r.runcommand("gin", "commit", "*.annex")
    # TODO: LC status should be something else?
    status["??"] -= nannex
    status["LC"] += nannex
    util.assert_status(r, status=status)

    out, err = r.runcommand("gin", "commit", ".")
    status["??"] -= ngit
    status["OK"] += ngit
    util.assert_status(r, status=status)

    # add some untracked files
    for idx in range(nuntracked):
        util.mkrandfile(f"untracked-{idx}", 70)
    status["??"] += nuntracked
    util.assert_status(r, status=status)

    r.login()

    # Upload does nothing
    out, err = r.runcommand("gin", "upload", exit=False)
    util.assert_status(r, status=status)
    assert err, "Expected error, got nothing"
    assert err == "[error] upload failed: no remote configured"

    # Upload should not add any new files
    out, err = r.runcommand("gin", "upload", ".", exit=False)
    util.assert_status(r, status=status)
    assert err, "Expected error, got nothing"
    assert err == "[error] upload failed: no remote configured"

    # gin upload command should not have created an extra commit
    assert util.getrevcount(r) == 3

    # modify all tracked files
    r.runcommand("gin", "unlock", ".")
    status["UL"] += nannex
    status["LC"] -= nannex
    util.assert_status(r, status=status)
    for idx in range(ngit):
        util.mkrandfile(f"root-{idx}.git", 4)
    for idx in range(nannex):
        util.mkrandfile(f"root-{idx}.annex", 2100)
    status["OK"] -= ngit
    status["MD"] += ngit
    util.assert_status(r, status=status)

    r.runcommand("gin", "lock", ".")
    status["LC"] += nannex
    status["UL"] = 0
    util.assert_status(r, status=status)

    # Commit all except untracked
    r.runcommand("gin", "commit", "*.annex", "*.git")
    status["LC"] = nannex
    status["MD"] = 0
    status["OK"] = ngit
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

    # Commit some files
    r.runcommand("gin", "commit", "subdir-c", "subdir-b/subfile-5.annex",
                 "subdir-b/subfile-9.annex", "subdir-f")
    status["LC"] += 22
    status["??"] -= 22
    util.assert_status(r, status=status)
    subb = util.zerostatus()
    subb["LC"] = 2
    subb["??"] = 8
    util.assert_status(r, path="subdir-b", status=subb)

    tenuntracked = util.zerostatus()
    tenuntracked["??"] = 10
    for idx in "ade":
        util.assert_status(r, path=f"subdir-{idx}", status=tenuntracked)

    # Unlock some files
    r.runcommand("gin", "unlock", "root-2.annex",
                 "root-7.annex", "root-3.annex")
    status["UL"] += 3
    status["LC"] -= 3
    util.assert_status(r, status=status)

    # Unlock a whole directory
    r.runcommand("gin", "unlock", "subdir-f")
    status["UL"] += 10
    status["LC"] -= 10
    util.assert_status(r, status=status)

    # Check subdirectory only
    tenul = util.zerostatus()
    tenul["UL"] = 10
    util.assert_status(r, path="subdir-f", status=tenul)

    # Check again from within the subdir
    r.cdrel("subdir-f")
    util.assert_status(r, status=tenul)
    r.cdrel("..")

    # Relock one of the files
    r.runcommand("gin", "lock", "root-3.annex")
    status["UL"] -= 1
    status["LC"] += 1
    util.assert_status(r, status=status)

    oneul = util.zerostatus()
    oneul["UL"] = 1
    # Check one of the remaining unlocked files explicitly
    util.assert_status(r, status=oneul, path="root-2.annex")

    status["NC"] = 0
    util.assert_status(r, status=status)

    # Remove a few file and check their status
    os.remove("subdir-f/subfile-1.annex")
    os.remove("root-10.git")
    shutil.rmtree("subdir-c")
    status["RM"] += 12
    status["OK"] -= 1  # root-10.git
    status["LC"] -= 10  # subdir-c
    status["UL"] -= 1  # subdir-f/subfile-1.annex was unlocked
    util.assert_status(r, status=status)

    # Do a gin ls on a deleted file
    onerm = util.zerostatus()
    onerm["RM"] = 1
    util.assert_status(r, path="root-10.git", status=onerm)

    # Commit deletions
    r.runcommand("gin", "commit",
                 "subdir-f/subfile-1.annex", "root-10.git", "subdir-c")
    status["RM"] = 0
    util.assert_status(r, status=status)

    # Add new files, remove some existing ones, check status and upload
    util.mkrandfile("new-annex-file", 10021)
    util.mkrandfile("new-git-file", 10)
    shutil.rmtree("subdir-f")
    status["RM"] += 9
    status["??"] += 2
    status["UL"] -= 9
    util.assert_status(r, status=status)

    print("Done!")


def test_create_remote_on_add(runner):
    r = runner
    r.runcommand("gin", "init")

    ngit = 3
    nannex = 2

    # create files in root
    for idx in range(ngit):
        util.mkrandfile(f"root-{idx}.git", 3)
    for idx in range(nannex):
        util.mkrandfile(f"root-{idx}.annex", 200)

    status = util.zerostatus()
    status["??"] = nannex + ngit
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", ".")
    status["OK"] = ngit
    status["LC"] = nannex
    status["??"] = 0
    util.assert_status(r, status=status)

    r.login()
    repopath = f"{r.username}/{r.reponame}"
    r.runcommand("gin", "add-remote", "--create", "origin", f"gin:{repopath}")

    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)


def test_create_remote_prompt(runner):
    r = runner
    r.runcommand("gin", "init")

    ngit = 3
    nannex = 2

    # create files in root
    for idx in range(ngit):
        util.mkrandfile(f"root-{idx}.git", 3)
    for idx in range(nannex):
        util.mkrandfile(f"root-{idx}.annex", 200)

    status = util.zerostatus()
    status["??"] = nannex + ngit
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", ".")
    status["OK"] = ngit
    status["LC"] = nannex
    status["??"] = 0
    util.assert_status(r, status=status)

    r.login()
    repopath = f"{r.username}/{r.reponame}"
    out, err = r.runcommand("gin", "add-remote", "origin", f"gin:{repopath}",
                            inp="abort", exit=False)
    assert err == "E: aborted"
    out, err = r.runcommand("git", "remote", "-v")
    assert not out, f"Expected empty output, got\n{out}"
    assert not err, f"Expected empty error, got\n{err}"

    out, err = r.runcommand("gin", "add-remote", "origin", f"gin:{repopath}",
                            inp="add anyway")
    out, err = r.runcommand("git", "remote", "-v")
    assert len(out.splitlines()) == 2, "Unexpected output"
    assert not err, f"Expected empty error, got\n{err}"

    out, err = r.runcommand("gin", "upload", exit=False)
    assert err, "Expected error, got nothing"

    r.runcommand("git", "remote", "rm", "origin")
    out, err = r.runcommand("gin", "add-remote", "origin", f"gin:{repopath}",
                            inp="create")
    out, err = r.runcommand("gin", "upload")

    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)


def test_add_gin_remote(runner):
    r = runner
    r.runcommand("gin", "init")

    ngit = 3
    nannex = 2

    # create files in root
    for idx in range(ngit):
        util.mkrandfile(f"root-{idx}.git", 3)
    for idx in range(nannex):
        util.mkrandfile(f"root-{idx}.annex", 200)

    status = util.zerostatus()
    status["??"] = nannex + ngit
    util.assert_status(r, status=status)

    r.runcommand("gin", "commit", ".")
    status["OK"] = ngit
    status["LC"] = nannex
    status["??"] = 0
    util.assert_status(r, status=status)

    r.login()
    r.runcommand("gin", "create", "--no-clone", r.reponame,
                 "Test repository for add remote")
    repopath = f"{r.username}/{r.reponame}"
    r.runcommand("gin", "add-remote", "origin", f"gin:{repopath}")

    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)
