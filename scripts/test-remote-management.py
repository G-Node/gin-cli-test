import os
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()
    # create repo locally only
    reponame = util.randrepo()
    localdir = f"{reponame}"
    os.mkdir(localdir)
    r.cdrel(localdir)

    yield r

    print(f"Cleaning up {reponame}")
    # cleanup
    r.runcommand("gin", "annex", "uninit", exit=False)


def test_local_only(runner):
    r = runner

    r.runcommand("gin", "init")

    # create files in root
    for idx in range(15):
        util.mkrandfile(f"root-{idx}.git", 1)
    for idx in range(10):
        util.mkrandfile(f"root-{idx}.annex", 100)

    util.assert_status(r, status={"??": 25})

    out, err = r.runcommand("gin", "commit", "*.annex")
    # TODO: LC status should be something else
    util.assert_status(r, status={"??": 15, "LC": 10})

    out, err = r.runcommand("gin", "commit", ".")
    util.assert_status(r, status={"OK": 15, "LC": 10})

    # TODO: Test all states

    print("Done!")
