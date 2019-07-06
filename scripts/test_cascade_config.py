import os
from runner import Runner
import util
import pytest
import yaml


@pytest.fixture
def runner():
    r = Runner()
    r.login()
    # create repo (remote and local) and cd into directory
    reponame = util.randrepo()
    print("Setting up test repository")
    r.runcommand("gin", "create", reponame,
                 "Test repository for cascading configurations")
    r.reponame = reponame
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    yield r

    r.cleanup()
    r.logout()


def test_config_path(runner):
    r = runner
    conf = dict()

    reporoot = os.path.join(r.testroot.name, r.reponame)
    localconffile = os.path.join(reporoot, "config.yml")

    def writelocalconf():
        with open(localconffile, "w") as conffile:
            conffile.write(yaml.dump(conf, default_flow_style=False))

    # Create local config file which sets annex threshold to 0kb
    conf["annex"] = {"minsize": "0kB"}
    writelocalconf()

    # small files should now be added to annex
    util.mkrandfile("smallfile", 1)
    r.runcommand("gin", "upload", "smallfile")
    # smallfile should be annexed
    assert util.isannexed(r, "smallfile")

    # .md file should still be excluded because of the exclusion rule in the
    # global configuration
    util.mkrandfile("anotherfile.md", 10)
    r.runcommand("gin", "upload", "anotherfile.md")
    # anotherfile.md should not be a symlink
    assert not util.isannexed(r, "anotherfile.md")

    # config file should never be added to annex
    r.runcommand("gin", "upload", "config.yml")
    assert not util.isannexed(r, "config.yml")

    # changing gitannex binary in local configuration should have no effect
    conf["bin"] = {"gitannex": "ls"}
    writelocalconf()

    util.mkrandfile("somefile", 1000)
    r.runcommand("gin", "commit", ".")
    r.runcommand("gin", "upload", ".")
