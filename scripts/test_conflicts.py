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
    locb.cleanup()
    loca.logout()


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


def test_download_git_over_untracked(runner):
    _untracked_conflict(runner, 10)


def test_download_annex_over_untracked(runner):
    _untracked_conflict(runner, 100)


def _tracked_conflict(runner, sizea, sizeb):
    loca, locb = runner

    # if a file involved in a pull conflict is in the annex, it will get
    # renamed and the error message will be different
    experr = acferrmsg if sizeb > 50 or sizea > 50 else cferrmsg

    fname = "dl_over_tracked"
    loca.cdrel()
    util.mkrandfile(fname, sizea)
    loca.runcommand("gin", "upload", fname)

    locb.cdrel()
    util.mkrandfile(fname, sizeb)
    locb.runcommand("gin", "commit", fname)
    out, err = locb.runcommand("gin", "download", exit=False)
    locb.runcommand("ls", "-l")
    assert err, "Expected error, got nothing"
    assert experr in err
    assert err.endswith(fname)


def test_download_git_over_git(runner):
    _tracked_conflict(runner, 10, 12)


def test_download_git_over_annex(runner):
    _tracked_conflict(runner, 11, 120)


def test_download_annex_over_git(runner):
    _tracked_conflict(runner, 100, 11)


def test_download_annex_over_annex(runner):
    _tracked_conflict(runner, 100, 120)


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
