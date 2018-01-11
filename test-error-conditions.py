import os
from random import randint
from runner import Runner
import util


def test_errors():
    norepoerr = "This command must be run from inside a gin repository."

    r = Runner()

    r.login()
    # username = r.username

    commands = [
        "upload",
        "download",
        "lock",
        "unlock",
        "get-content",
        "remove-content",
    ]

    # Unable to run any git commands outside a git repository
    for cmd in commands:
        # On directory
        out, err = r.runcommand("gin", cmd, ".", exit=False)
        assert err == norepoerr

        # On specific file
        out, err = r.runcommand("gin", cmd, "foobar", exit=False)
        assert err == norepoerr

    # create repo (remote and local) and cd into directory
    reponame = f"gin-test-{randint(0, 9999):04}"
    # repopath = f"{username}/{reponame}"
    r.runcommand("gin", "create", reponame,
                 "Test repository for error output. Created with test scripts")
    r.cdrel(reponame)

    # Unable to run any command on file that does not exist (download ignored)
    out, err = r.runcommand("gin", "upload", "foobar", exit=False)
    assert out == "No files matched foobar"
    assert err == "1 operation failed"
    for cmd in commands[2:]:
        out, err = r.runcommand("gin", cmd, "foobar", exit=False)
        assert out == "No files matched foobar"
        assert err == "1 operation failed"

    # make a few annex and git files
    os.mkdir("smallfiles")
    r.cdrel("smallfiles")
    for idx in range(20):
        util.mkrandfile(f"smallfile-{idx:03}", 20)
    r.cdrel("..")
    os.mkdir("datafiles")
    r.cdrel("datafiles")
    for idx in range(5):
        util.mkrandfile(f"datafile-{idx:03}", 2000)
    r.cdrel("..")

    # No output on lock, unlock, getc, rmc on untracked file(s)
    for cmd in commands[2:]:
        out, err = r.runcommand("gin", cmd, "smallfiles", exit=False)
        assert not out
        assert not err

        out, err = r.runcommand("gin", cmd, "datafiles", exit=False)
        assert not out
        assert not err

        out, err = r.runcommand("gin", cmd, "datafiles/*", exit=False)
        assert not out
        assert not err

    out, err = r.runcommand("gin", "upload", "smallfiles")
    assert out, "Expected output, got nothing"
    assert not err

    # No output on lock, unlock, getc, rmc on non-annexed file(s)
    for cmd in commands[2:]:
        out, err = r.runcommand("gin", cmd, "smallfiles", exit=False)
        assert not out
        assert not err

    out, err = r.runcommand("gin", "upload", "datafiles")
    out, err = r.runcommand("gin", "rmc", "datafiles")

    # Unable to unlock without content
    out, err = r.runcommand("gin", "unlock", "datafiles", exit=False)
    errlines = err.splitlines()
    for line in errlines[:-1]:
        assert line.strip().endswith("Content not available locally")
    assert errlines[-1].strip() == "5 operations failed"

    # TODO: Change server address and try go get-content

    # TODO: Figure out how to simulate not-enough-free-space

    # Creating repository that already exists
    r.cdrel("..")

    out, err = r.runcommand("gin", "create", reponame, exit=False)
    assert err == ("invalid repository name or repository with the same name"
                   " already exists")

    # Creating repository but local directory already exists (non-empty)
    anotherrepo = f"gin-test-{randint(0, 9999):04}"
    print(f"Creating directory '{anotherrepo}'")
    os.mkdir(anotherrepo)
    util.mkrandfile(os.path.join(anotherrepo, f"hold"), 20)

    out, err = r.runcommand("gin", "create", anotherrepo, exit=False)
    assert ("Creating repository" in out
            and "OK" in out), f"Failed to create {anotherrepo} on server"
    assert out.endswith(
        f"Repository download failed. '{anotherrepo}' already exists in the "
        "current directory and is not empty."
    )
    assert err == "1 operation failed"

    out, err = r.runcommand("gin", "repos")
    assert anotherrepo in out

    r.cleanup(reponame)
    r.logout()

    print("DONE!")
