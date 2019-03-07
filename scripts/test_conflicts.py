import os
import tempfile
from runner import Runner
import util
import pytest


uperrmsg = ("upload failed: changes were made on the server that have not "
            "been downloaded; run 'gin download' to update local copies")
owerrmsg = ("download failed: local modified or untracked files would be "
            "overwritten by download")
cferrmsg = ("download failed: files changed locally and remotely "
            "and cannot be automatically merged (merge conflict)")
acferrmsg = ("files changed locally and remotely. Both files have been kept:")


def server_remotes():
    # Use 2 runner instances to checkout two clones and create merge conflicts
    loca = Runner()
    loca.login()
    locb = Runner()
    locb.env = loca.env  # share environments between the two users

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

    return (loca, locb)


def dir_remotes(remoteloc):
    # Use 2 runner instances to checkout two clones and create merge conflicts
    loca = Runner()

    reponame = util.randrepo()
    os.mkdir(reponame)
    loca.cdrel(reponame)

    # Create repo in A
    loca.runcommand("gin", "init")
    loca.runcommand("gin", "add-remote", "--create", "--default",
                    "origin", f"dir:{remoteloc.name}")
    loca.runcommand("gin", "upload")
    loca.repositories[loca.cmdloc] = None

    # Init in B and download
    locb = Runner()
    os.mkdir(reponame)
    locb.cdrel(reponame)
    locb.runcommand("gin", "init")
    locb.runcommand("gin", "add-remote", "--default",
                    "origin", f"dir:{remoteloc.name}")
    locb.runcommand("gin", "download")
    locb.repositories[locb.cmdloc] = None

    return (loca, locb)


@pytest.fixture
def runner(rtype):
    if rtype == "server":
        print("Running server test")
        loca, locb = server_remotes()
    elif rtype == "directory":
        print("Running directory test")
        tmp = tempfile.TemporaryDirectory(prefix="gintest-remote")
        loca, locb = dir_remotes(tmp)
    else:
        # default to remote
        loca, locb = server_remotes()

    yield (loca, locb)
    loca.cleanup()
    locb.cleanup()


def _untracked_conflict(runner, size):
    loca, locb = runner

    fname = "dl_over_untracked"
    loca.cdrel()
    util.mkrandfile(fname, size)
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    util.mkrandfile(fname, size+(size//10))
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert owerrmsg in err
    assert err.endswith(fname)

    # resolution: rename untracked file and download
    locb.cdrel()
    os.rename(fname, fname+".bak")
    locb.runcommand("gin", "download")


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_git_over_untracked(runner):
    _untracked_conflict(runner, 10)


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_annex_over_untracked(runner):
    _untracked_conflict(runner, 100)


def _tracked_conflict(runner, sizea, sizeb):
    loca, locb = runner

    # if a file involved in a pull conflict is in the annex, it will get
    # renamed and the error message will be different
    annexed = sizea > 50 or sizeb > 50
    experr = acferrmsg if annexed else cferrmsg

    fname = "dl_over_tracked"
    loca.cdrel()
    util.mkrandfile(fname, sizea)
    loca.runcommand("gin", "upload", fname)
    hasha = util.md5sum(fname)

    locb.cdrel()
    util.mkrandfile(fname, sizeb)
    hashb = util.md5sum(fname)
    locb.runcommand("gin", "commit", fname)
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert experr in err
    assert err.endswith(fname)

    if not annexed:
        # resolution: rename file and sync
        locb.cdrel()
        os.rename(fname, fname+".bak")
        locb.runcommand("gin", "annex", "sync")
        assert hasha == util.md5sum(fname)
        assert hashb == util.md5sum(fname+".bak")


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_git_over_git(runner):
    _tracked_conflict(runner, 10, 12)


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_git_over_annex(runner):
    _tracked_conflict(runner, 11, 120)


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_annex_over_git(runner):
    _tracked_conflict(runner, 100, 11)


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_annex_over_annex(runner):
    _tracked_conflict(runner, 100, 120)


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_download_text_over_text(runner):
    loca, locb = runner

    fname = "text_over_text"
    loca.cdrel()
    with open(fname, "w") as txtfile:
        txtfile.write("I AM A")
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    with open(fname, "w") as txtfile:
        txtfile.write("I AM B")
    locb.runcommand("gin", "commit", fname)
    out, err = locb.runcommand("gin", "download", exit=False)
    with open(fname, "r") as txtfile:
        print(txtfile.read())
    assert err, "Expected error, got nothing"
    assert cferrmsg in err
    assert err.endswith(fname)

    # resolution: rename file and sync
    locb.cdrel()
    os.rename(fname, fname+".bak")
    locb.runcommand("gin", "annex", "sync")

    # make sure the files haven't changed
    with open(fname) as txtfile:
        assert txtfile.read() == "I AM A"
    with open(fname+".bak") as txtfile:
        assert txtfile.read() == "I AM B"


@pytest.mark.parametrize("rtype", ["directory", "server"])
def test_push_conflict(runner):
    loca, locb = runner

    loca.cdrel()
    util.mkrandfile("newfile.git", 1)
    loca.runcommand("gin", "upload", "newfile.git")
    locb.cdrel()
    util.mkrandfile("newfile-b.git", 1)
    out, err = locb.runcommand("gin", "upload", "newfile-b.git", exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(uperrmsg)

    locb.runcommand("gin", "download")
    locb.runcommand("gin", "upload", "newfile-b.git")
