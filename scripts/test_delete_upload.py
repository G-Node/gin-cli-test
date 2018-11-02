import os
from runner import Runner
import util
import pytest


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


def test_workflow(runner):
    r = runner

    # create files in root
    gitfiles = list()
    for idx in range(8):
        fname = f"root-{idx}.git"
        util.mkrandfile(fname, 5)
        gitfiles.append(fname)

    annexfiles = list()
    for idx in range(5):
        fname = f"root-{idx}.annex"
        annexfiles.append(fname)
        util.mkrandfile(fname, 2000)

    # upload
    r.runcommand("gin", "upload", ".")

    # delete a git file and "upload" it
    os.unlink(gitfiles[-1])
    r.runcommand("gin", "upload", gitfiles[-1])
    gitfiles = gitfiles[:-1]

    # delete an annex file and "upload" it
    os.unlink(annexfiles[-1])
    r.runcommand("gin", "upload", annexfiles[-1])
    annexfiles = annexfiles[:-1]

    # delete everything and upload, naming all deleted files
    allfiles = gitfiles + annexfiles
    for fn in allfiles:
        os.unlink(fn)

    r.runcommand("gin", "upload", *allfiles)
