import os
import shutil
from runner import Runner
import util
import tempfile
import pytest


@pytest.fixture
def runner():
    r = Runner()
    # change config dir to some temporary directory with spaces in the name
    defaultconfdir = r.env["GIN_CONFIG_DIR"]
    conftemp = tempfile.TemporaryDirectory(prefix="conf place with spaces")
    spaceconfdir = os.path.join(conftemp.name, "conf")
    r.env["GIN_CONFIG_DIR"] = spaceconfdir
    shutil.copytree(defaultconfdir, spaceconfdir)
    r.login()
    # create repo (remote and local) and cd into directory
    reponame = util.randrepo()
    print("Setting up test repository")
    r.runcommand("gin", "create", reponame,
                 "Test repository for alt config path (with spaces)",
                 echo=False)
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


def test_config_path(runner):
    # upload a few files just to make sure it's all good
    util.mkrandfile("file21", 10000)
    util.mkrandfile("file22", 10)
    runner.runcommand("gin", "upload", "file21", "file22")
