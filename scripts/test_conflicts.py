import os
from runner import Runner
import util
import pytest


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


def test_download_over_modified(runner):
    loca, locb = runner
    # create files in root (loca)
    loca.cdrel()
    for idx in range(5):
        util.mkrandfile(f"root-{idx}.git", 1)
    for idx in range(3):
        util.mkrandfile(f"root-{idx}.annex", 100)

    # Create some subdirectories with files (loca)
    for idx in "abcdef":
        dirname = f"subdir-{idx}"
        os.mkdir(dirname)
        loca.cdrel(dirname)
        for jdx in range(2):
            util.mkrandfile(f"subfile-{jdx}.annex", 200)
        loca.cdrel("..")

    # upload should do nothing
    out, err = loca.runcommand("gin", "upload", ".")

    loca.runcommand("gin", "download")
    loca.runcommand("gin", "upload", ".")

    locb.runcommand("gin", "download")

    expmsg = ("upload failed: changes were made on the server that have not "
              "been downloaded; run 'gin download' to update local copies")

    # A PUSH, B PUSH BEFORE PULL
    loca.cdrel()
    util.mkrandfile("newfile", 10)
    loca.runcommand("gin", "upload", "newfile")
    locb.cdrel()
    util.mkrandfile("newfile-b", 30)
    out, err = locb.runcommand("gin", "upload", "newfile-b", exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(expmsg)

    # A PUSH, B PUSH SAME NAME FILE
    pushconflict = "push-conflict.annex"
    loca.cdrel()
    util.mkrandfile(pushconflict, 100)

    locb.cdrel()
    util.mkrandfile(pushconflict, 100)

    loca.runcommand("gin", "upload", pushconflict)
    out, err = locb.runcommand("gin", "upload", pushconflict, exit=False)
    assert err, "Expected error, got nothing"
    assert out.endswith(expmsg)

    # DOWNLOAD FILE THAT EXISTS LOCALLY
    pullconflict = "pull-conflict.annex"
    loca.cdrel()
    util.mkrandfile(pullconflict, 100)
    loca.runcommand("gin", "upload", pullconflict)

    locb.cdrel()
    util.mkrandfile(pullconflict, 50)

    print(f"{loca.cmdloc} commit: {util.getrevcount(loca)}")
    print(f"{locb.cmdloc} commit: {util.getrevcount(locb)}")
    out, err = locb.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    expmsg = ("download failed: local modified or untracked files would be "
              "overwritten by download")
    assert expmsg in err
    assert err.endswith(pullconflict)
    print("Done!")
