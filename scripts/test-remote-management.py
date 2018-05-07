import os
from runner import Runner
import util


def test_local_only():
    r = Runner()
    # create repo locally only
    reponame = util.randrepo()
    localdir = f"{reponame}"
    os.mkdir(localdir)
    r.cdrel(localdir)

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

    # cleanup
    r.runcommand("gin", "annex", "uninit", exit=False)

    print("Done!")
