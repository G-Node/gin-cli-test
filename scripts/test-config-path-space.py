import os
import shutil
from random import randint
from runner import Runner
import util
import tempfile


def test_config_path():
    r = Runner()

    # change config dir to some temporary directory with spaces in the name

    # Change gin and git server address:port in config and test failures
    defaultconfdir = r.env["GIN_CONFIG_DIR"]
    conftemp = tempfile.TemporaryDirectory(prefix="conf place with spaces")
    spaceconfdir = os.path.join(conftemp.name, "conf")
    r.env["GIN_CONFIG_DIR"] = spaceconfdir
    shutil.copytree(defaultconfdir, spaceconfdir)

    r.login()

    # create repo (remote and local) and cd into directory
    reponame = f"gin-test-{randint(0, 9999):04}"
    r.runcommand("gin", "create", reponame,
                 "Test repository for error output. Created with test scripts")
    r.cdrel(reponame)

    # upload a few files just to make sure it's all good
    util.mkrandfile("file21", 10000)
    util.mkrandfile("file22", 10)

    r.runcommand("gin", "upload", "file21", "file22")

    r.cleanup(reponame)
    r.logout()

    print("DONE!")
