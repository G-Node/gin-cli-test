import os
import shutil
from random import randint
from runner import Runner
import util
import tempfile
import pytest


@pytest.fixture(scope="module")
def runner():
    r = Runner()
    # Change gin and git server address:port in config and test failures
    defaultconfdir = r.env["GIN_CONFIG_DIR"]
    conftemp = tempfile.TemporaryDirectory(prefix="conf place with spaces")
    spaceconfdir = os.path.join(conftemp.name, "conf")
    r.env["GIN_CONFIG_DIR"] = spaceconfdir
    shutil.copytree(defaultconfdir, spaceconfdir)
    r.login()
    # create repo (remote and local) and cd into directory
    reponame = f"gin-test-{randint(0, 9999):04}"
    # repopath = f"{username}/{reponame}"
    print("Setting up test repository")
    r.runcommand("gin", "create", reponame,
                 "Test repository for cascading configurations",
                 echo=False)
    r.cdrel(reponame)

    yield r

    print(f"Cleaning up {reponame}")
    r.cleanup(reponame)
    r.logout()


def test_config_path(runner):
    # upload a few files just to make sure it's all good
    util.mkrandfile("file21", 10000)
    util.mkrandfile("file22", 10)
    runner.runcommand("gin", "upload", "file21", "file22")
    print("DONE!")
