import os
from runner import Runner
import util
import pytest


uperrmsg = ("upload failed: changes were made on the server that have not "
            "been downloaded; run 'gin download' to update local copies")
owerrmsg = ("download failed: local modified or untracked files would be "
            "overwritten by download")
cferrmsg = ("download failed: files changed locally and remotely "
            "and cannot be automatically merged (merge conflict)")


@pytest.fixture
def runner():
    # Use 2 runner instances to checkout two clones and create merge conflicts
    loca = Runner()
    locb = Runner()
    # No need to login for b: Use same config and machine; shouldn't matter
    loca.login()

    # create repo (remote and local) and cd into directory
    reponame = util.randrepo()
    repopath = f"{loca.username}/{reponame}"

    # Create repo in A
    loca.runcommand("gin", "create", reponame,
                    "Repository for testing merge conflicts")
    loca.cdrel(reponame)
    loca.repositories[loca.cmdloc] = reponame
    # Clone into B
    locb.runcommand("gin", "get", repopath)
    locb.cdrel(reponame)
    locb.repositories[locb.cmdloc] = None

    yield (loca, locb)

    loca.cleanup()
    loca.logout()
    locb.runcommand("git", "annex", "uninit")


def test_download_over_untracked(runner):
    loca, locb = runner

    # DOWNLOAD FILE THAT EXISTS LOCALLY (UNTRACKED)
    fname = "pull-conflict.annex"
    loca.cdrel()
    util.mkrandfile(fname, 100)
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    util.mkrandfile(fname, 50)

    # print(f"{loca.cmdloc} commit: {util.getrevcount(loca)}")
    # print(f"{locb.cmdloc} commit: {util.getrevcount(locb)}")
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert owerrmsg in err
    assert err.endswith(fname)


def test_download_over_modified_git(runner):
    loca, locb = runner

    # DOWNLOAD FILE THAT IS UNTRACKED LOCALLY (COMMITTED)
    fname = "pull-conflict.git"
    loca.cdrel()
    util.mkrandfile(fname, 10)
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    locb.runcommand("gin", "download")

    loca.cdrel()
    util.mkrandfile(fname, 10)  # modify existing file in A
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    util.mkrandfile(fname, 15)  # modify existing file in B
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert owerrmsg in err
    assert err.endswith(fname)


def test_download_over_modified_annex(runner):
    loca, locb = runner

    # DOWNLOAD FILE THAT IS UNTRACKED LOCALLY (COMMITTED)
    fname = "pull-conflict.annex"
    loca.cdrel()
    util.mkrandfile(fname, 200)
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    locb.runcommand("gin", "download", "--content")

    loca.cdrel()
    loca.runcommand("gin", "unlock", fname)
    util.mkrandfile(fname, 300)  # modify existing file in A
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    locb.runcommand("gin", "unlock", fname)
    util.mkrandfile(fname, 150)  # modify existing file in B
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert owerrmsg in err
    assert err.endswith(fname)


def test_download_over_modified_text(runner):
    loca, locb = runner

    # DOWNLOAD TEXT FILE MERGE CONFLICT
    loca.cdrel()
    fname = "mergeconflict.git"
    with open(fname) as txtfile:
        txtfile.write("I AM A")
    loca.runcommand("gin", "upload", fname)

    out, err = locb.runcommand("gin", "download", exit=False)
    print(out)
    print(err)
    assert err, "Expected error, got nothing"
    assert out.endswith(cferrmsg)


def test_upload_conflict_text(runner):
    loca, locb = runner

    # A PUSH, B PUSH BEFORE PULL (git simple text file)
    loca.cdrel()
    with open("textfile", "w") as txtfile:
        txtfile.write("I AM A")
    loca.runcommand("gin", "upload", "textfile")
    locb.cdrel()
    with open("textfile", "w") as txtfile:
        txtfile.write("I AM B")
    out, err = locb.runcommand("gin", "upload", "textfile", exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(uperrmsg)


def test_upload_conflict_git(runner):
    loca, locb = runner

    # A PUSH, B PUSH BEFORE PULL (git)
    loca.cdrel()
    util.mkrandfile("newfile.git", 1)
    loca.runcommand("gin", "upload", "newfile.git")
    locb.cdrel()
    util.mkrandfile("newfile-b.git", 1)
    out, err = locb.runcommand("gin", "upload", "newfile-b.git", exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(uperrmsg)


def test_upload_conflict_annex(runner):
    loca, locb = runner

    # A PUSH, B PUSH BEFORE PULL (annex)
    loca.cdrel()
    util.mkrandfile("newfile.annex", 10)
    loca.runcommand("gin", "upload", "newfile.annex")
    locb.cdrel()
    util.mkrandfile("newfile-b.annex", 30)
    out, err = locb.runcommand("gin", "upload", "newfile-b.annex", exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(uperrmsg)


def test_upload_conflict_samefile(runner):
    loca, locb = runner

    # A PUSH, B PUSH SAME NAME FILE
    fname = "push-conflict.annex"
    loca.cdrel()
    util.mkrandfile(fname, 100)

    locb.cdrel()
    util.mkrandfile(fname, 100)

    loca.runcommand("gin", "upload", fname)
    out, err = locb.runcommand("gin", "upload", fname, exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(uperrmsg)

    print("Done!")
