import os
import shutil
from runner import Runner
import util
import pytest
import json
import socket


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

    # cleanup
    r.cleanup()
    r.logout()


def test_local_only(runner):
    r = runner
    r.runcommand("gin", "init")
    r.repositories[r.cmdloc] = None

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
    r.repositories[r.cmdloc] = None

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
    r.repositories[r.cmdloc] = None

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
                            inp="abort")
    assert not err, f"Expected empty error, got\n{err}"
    assert out.endswith("aborted")
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
    r.repositories[r.cmdloc] = None

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
    r.repositories[r.cmdloc] = r.reponame
    repopath = f"{r.username}/{r.reponame}"
    r.runcommand("gin", "add-remote", "origin", f"gin:{repopath}")
    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)

    # remove remote, add it with a different name (not origin) and see if it
    # works
    util.mkrandfile(f"final-file.annex", 500)
    r.runcommand("gin", "git", "remote", "rm", "origin")
    r.runcommand("gin", "git", "config", "--unset", "gin.remote")
    r.runcommand("gin", "add-remote", "notorigin", f"gin:{repopath}")
    r.runcommand("gin", "upload", "final-file.annex")
    status["OK"] += 1
    util.assert_status(r, status=status)


def test_add_directory_remote(runner):
    r = runner
    r.runcommand("gin", "init")
    r.repositories[r.cmdloc] = None

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

    fsremotedir = os.path.join(r.testroot.name, "annexdata")
    r.runcommand("gin", "add-remote", "--create",
                 "lanbackup", f"dir:{fsremotedir}")
    r.runcommand("gin", "git", "remote", "-v")
    r.repositories[fsremotedir] = None

    r.runcommand("gin", "upload")
    status["OK"] += status["LC"]
    status["LC"] = 0
    util.assert_status(r, status=status)

    # TODO: Test cloning from a different location, uploading, and downloading


def assert_locations(r, expected):
    out, err = r.runcommand("git", "annex", "whereis",
                            "--json", echo=False)
    for line in out.splitlines():
        item = json.loads(line)
        fname = item["file"]
        locs = [f["description"] for f in item["whereis"]]
        assert sorted(expected[fname]) == sorted(locs)


def test_multiple_remotes_gitanddir(runner):
    r = runner
    r.login()
    r.runcommand("gin", "create", "--here", r.reponame, "Multi-remote test")
    r.repositories[r.cmdloc] = r.reponame

    here = f"{r.username}@{socket.gethostname()}"

    # add a directory remote
    fsremotedir = os.path.join(r.testroot.name, "annexdata")
    out, err = r.runcommand("gin", "add-remote", "--create",
                            "datastore", f"dir:{fsremotedir}")
    r.repositories[fsremotedir] = None
    assert "Default remote: origin" in out

    out, err = r.runcommand("gin", "git", "config", "--get", "gin.remote")
    assert out.strip() == "origin"

    ngit = 5
    nannex = 3

    contentlocs = dict()
    for idx in range(ngit):
        fname = f"gitfile{idx}"
        util.mkrandfile(fname, 3)
    for idx in range(nannex):
        fname = f"annexfile{idx}"
        util.mkrandfile(fname, 900)
        contentlocs[fname] = list()

    r.runcommand("gin", "upload", "gitfile*")
    assert_locations(r, contentlocs)

    def revcountremote(remote):
        n, _ = r.runcommand("git", "rev-list", "--count",
                            f"{remote}/master", "--")
        return int(n)

    # commits are always pushed to all remotes
    assert revcountremote("origin") == revcountremote("datastore") == 2

    r.runcommand("gin", "upload", "annexfile*")
    for fname in contentlocs:
        if "annexfile" in fname:
            contentlocs[fname].extend(["origin", here])
    assert_locations(r, contentlocs)
    assert revcountremote("origin") == revcountremote("datastore") == 3

    # upload annexfile0 to datastore
    r.runcommand("gin", "upload", "--to", "datastore", "annexfile0")
    contentlocs["annexfile0"].append("GIN Storage [datastore]")
    assert_locations(r, contentlocs)

    # upload everything to datastore
    r.runcommand("gin", "upload", "--to", "datastore")
    for fname, locs in contentlocs.items():
        if "GIN Storage [datastore]" not in locs:
            contentlocs[fname].append("GIN Storage [datastore]")
    assert_locations(r, contentlocs)
    assert revcountremote("origin") == revcountremote("datastore") == 3

    util.mkrandfile("another annex file", 1000)
    r.runcommand("gin", "upload", "--to", "datastore", "another annex file")
    contentlocs["another annex file"] = ["GIN Storage [datastore]", here]
    assert_locations(r, contentlocs)
    assert revcountremote("origin") == revcountremote("datastore") == 4

    # add another directory remote
    fsremotedir = os.path.join(r.testroot.name, "annexdata-two")
    out, err = r.runcommand("gin", "add-remote", "--create",
                            "lanstore", f"dir:{fsremotedir}")
    r.repositories[fsremotedir] = None
    assert "Default remote: origin" in out

    for idx in range(5):
        fname = f"moredata{idx}"
        contentlocs[fname] = list()
        util.mkrandfile(fname, 1000)

    # commit only
    r.runcommand("gin", "commit", "moredata*")
    for fname in contentlocs:
        if "moredata" in fname:
            contentlocs[fname].append(here)
    assert_locations(r, contentlocs)

    # upload only to non-gin remotes
    r.runcommand("gin", "upload", "--to", "datastore", "--to", "lanstore",
                 "moredata*")
    assert (revcountremote("origin") == revcountremote("datastore")
            == revcountremote("lanstore") == 5)
    newlocs = ["GIN Storage [datastore]", "GIN Storage [lanstore]"]
    for fname in contentlocs:
        if "moredata" in fname:
            contentlocs[fname].extend(newlocs)
    assert_locations(r, contentlocs)

    # change default to datastore
    out, err = r.runcommand("gin", "use-remote")
    assert out.strip() == ":: Default remote: origin"
    out, err = r.runcommand("gin", "remotes")
    outlines = out.splitlines()
    assert len(outlines) == 4
    for line in outlines:
        if "origin" in line:
            assert "[default]" in line

    r.runcommand("gin", "use-remote", "datastore")
    out, err = r.runcommand("gin", "use-remote")
    assert out.strip() == ":: Default remote: datastore"

    dsfname = "send-me-to-the-datastore"
    util.mkrandfile(dsfname, 1024)
    r.runcommand("gin", "upload", dsfname)
    contentlocs[dsfname] = [here, "GIN Storage [datastore]"]
    assert_locations(r, contentlocs)

    # upload everything everywhere
    r.runcommand("gin", "upload", "--to", "all", ".")
    allremotes = [here, "origin",
                  "GIN Storage [datastore]", "GIN Storage [lanstore]"]
    for fname in contentlocs:
        contentlocs[fname] = allremotes
    assert_locations(r, contentlocs)
