import os
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()
    r.login()

    reponame = util.randrepo()
    r.reponame = reponame

    localdir = f"{reponame}-local-clone"
    os.mkdir(localdir)
    r.cdrel(localdir)

    yield r

    r.cleanup()
    r.logout()


def test_create_from_local(runner):
    r = runner
    # create files in root
    for idx in range(51):
        util.mkrandfile(f"root-{idx}.git", 1)
    for idx in range(70, 91):
        util.mkrandfile(f"root-{idx}.annex", 100)

    # Create from local directory
    r.runcommand("gin", "create", "--here", r.reponame,
                 "Test repository for create --here. Created with test script")
    r.runcommand("gin", "upload", ".")
    util.assert_status(r, status={"OK": 72})
    r.repositories[r.cmdloc] = r.reponame

    # gin upload command should not have created an extra commit
    out, err = r.runcommand("gin", "git", "rev-list", "--count", "HEAD")
    assert int(out) == 2, f"Expected 2 commits, got {out}"

    # Create more root files that will remain UNTRACKED
    for c in "abcdef":
        util.mkrandfile(f"root-file-{c}.untracked")

    # Create some subdirectories with files
    for idx in "abcdef":
        dirname = f"subdir-{idx}"
        os.mkdir(dirname)
        r.cdrel(dirname)
        for jdx in range(1, 11):
            util.mkrandfile(f"subfile-{jdx}.annex", 200)
        r.cdrel("..")

    # Upload all the files of the first subdirectory and 2 from the second
    r.runcommand("gin", "upload", "subdir-a", "subdir-b/subfile-5.annex",
                 "subdir-b/subfile-10.annex")

    status = {"OK": 84, "??": 54}
    util.assert_status(r, status=status)

    # can also check each directory individually
    subb = {"??": 8}
    util.assert_status(r, path="subdir-b", status=subb)
    subcdef = {"??": 10}
    for p in "cdef":
        util.assert_status(r, path=f"subdir-{p}", status=subcdef)

    # Lock some files
    r.runcommand("gin", "lock", "root-70.annex",
                 "root-75.annex", "root-84.annex")

    # Locked files should be marked TC
    util.assert_status(r, status={"TC": 3})

    # Lock a whole directory
    r.runcommand("gin", "lock", "subdir-a")
    util.assert_status(r, status={"TC": 13})

    # Check subdirectory only
    util.assert_status(r, path="subdir-a", status={"TC": 10})

    # Check again but from within the subdir
    r.cdrel("subdir-a")
    util.assert_status(r, status={"TC": 10})
    r.cdrel("..")

    # Re-unlock one of the files
    r.runcommand("gin", "unlock", "root-84.annex")
    util.assert_status(r, status={"TC": 12})

    # check one of the remaining unlocked files explicitly
    util.assert_status(r, path="root-70.annex", status={"TC": 1})

    # commit the type changes
    r.runcommand("gin", "commit")
    # no TCs left
    util.assert_status(r, status={"TC": 0})

    # There should be no NC files so far
    util.assert_status(r, status={"NC": 0})

    # drop some files and check the counts
    r.runcommand("gin", "rmc", "subdir-b/subfile-5.annex")
    util.assert_status(r, path="subdir-b", status={"NC": 1})

    r.runcommand("gin", "rmc", "subdir-b")
    util.assert_status(r, path="subdir-b", status={"NC": 2})

    r.runcommand("gin", "remove-content", "subdir-a")
    util.assert_status(r, path="subdir-b", status={"NC": 2})
    util.assert_status(r, path="subdir-a", status={"NC": 10})
    util.assert_status(r, status={"NC": 12})

    print("Done!")
