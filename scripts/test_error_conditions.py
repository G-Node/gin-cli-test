import os
import shutil
import yaml
from random import randint
from runner import Runner
import util
import tempfile
import pytest


@pytest.fixture
def runner():
    r = Runner()
    r.login()
    # username = r.username
    # create repo (remote and local) and cd into directory
    reponame = util.randrepo()
    # repopath = f"{username}/{reponame}"
    r.runcommand("gin", "create", reponame,
                 "Test repository for error output. Created with test scripts")
    r.reponame = reponame
    r.repositories[r.cmdloc] = reponame

    r.cdrel(reponame)
    r.runcommand("gin", "upload")
    r.cdrel("..")

    yield r

    r.cleanup()
    r.logout()


def test_errors(runner):
    r = runner
    norepoerr = "[error] this command must be run from inside a gin repository"

    commands = [
        "upload",
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

    out, err = r.runcommand("gin", "download", exit=False)
    assert err == norepoerr

    r.cdrel(r.reponame)

    # Unable to run any command on file that does not exist
    out, err = r.runcommand("gin", "upload", "foobar", exit=False)
    assert out.endswith("   Nothing to do")
    for cmd in commands[1:]:
        out, err = r.runcommand("gin", cmd, "foobar", exit=False)
        assert out.endswith("No files matched foobar")
        assert err == "[error] 1 operation failed"

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

    # Nothing to do on lock, unlock, getc, rmc on untracked file(s)
    nothingmsg = "   Nothing to do"
    for cmd in commands[1:]:
        out, err = r.runcommand("gin", cmd, "smallfiles", exit=False)
        assert out.endswith(nothingmsg)
        assert not err

        out, err = r.runcommand("gin", cmd, "datafiles", exit=False)
        assert out.endswith(nothingmsg)
        assert not err

        out, err = r.runcommand("gin", cmd, "datafiles/*", exit=False)
        assert out.endswith(nothingmsg)
        assert not err

    out, err = r.runcommand("gin", "upload", "smallfiles")
    assert out, "Expected output, got nothing"
    assert not err

    # Nothing to do on lock, unlock, getc, rmc on non-annexed file(s)
    for cmd in commands[1:]:
        out, err = r.runcommand("gin", cmd, "smallfiles", exit=False)
        assert out.endswith(nothingmsg)
        assert not err

    out, err = r.runcommand("gin", "upload", "datafiles")

    # unlock, commit, modify, and lock before commit
    r.runcommand("gin", "unlock", "datafiles")
    r.runcommand("gin", "annex", "sync")
    # r.runcommand("gin", "commit", "datafiles")

    r.runcommand("ls", "-l", "datafiles")
    # modify the files
    for idx in range(3):
        util.mkrandfile(os.path.join("datafiles", f"datafile-{idx:03}"), 2000)

    out, err = r.runcommand("gin", "lock", "datafiles", exit=False)
    assert "Locking this file would discard" in out
    assert err == "[error] 3 operations failed"

    r.runcommand("gin", "upload", ".")
    r.runcommand("gin", "lock", ".")

    r.runcommand("gin", "rmc", "datafiles")

    # change git repo remote address/port and test get-content failure
    out, err = r.runcommand("git", "remote", "-v")
    name, address, *_ = out.split()
    address = address.replace("2222", "1111")
    r.runcommand("git", "remote", "set-url", name, address)

    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    for line in errlines[:-1]:
        assert line.strip().endswith("(content or server unavailable)")
    assert errlines[-1].strip() == "[error] 5 operations failed"

    # revert remote change
    address = address.replace("1111", "2222")
    r.runcommand("git", "remote", "set-url", name, address)

    # Change gin and git server address:port in config and test failures
    goodconfdir = r.env["GIN_CONFIG_DIR"]
    badconftemp = tempfile.TemporaryDirectory(prefix="badconf")
    badconfdir = os.path.join(badconftemp.name, "conf")
    r.env["GIN_CONFIG_DIR"] = badconfdir
    shutil.copytree(goodconfdir, badconfdir)
    with open(os.path.join(goodconfdir, "config.yml")) as conffile:
        confdata = yaml.load(conffile.read(), Loader=yaml.CSafeLoader)

    confdata["servers"]["gin"]["web"]["port"] = 1
    confdata["servers"]["gin"]["git"]["port"] = 1
    with open(os.path.join(badconfdir, "config.yml"), "w") as conffile:
        conffile.write(yaml.dump(confdata))
    out, err = r.runcommand("gin", "create", "ThisShouldFail", exit=False)
    assert err, "Expected error, got nothing"
    errmsg = "[error] server refused connection"
    assert err == errmsg

    # TODO: simulate not-enough-free-space

    # Recover good config
    r.env["GIN_CONFIG_DIR"] = goodconfdir

    # delete all keys (there might be leftovers from aborted tests)
    err = ""
    while len(err) == 0:
        out, err = r.runcommand("gin", "keys", "--delete", "1", exit=False)

    # get content should fail now
    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    for line in errlines[:-1]:
        # TODO: Should print auth error
        assert line.strip().endswith("(content or server unavailable)")
    assert errlines[-1].strip() == "[error] 5 operations failed"

    out, err = r.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    assert len(errlines) == 1
    assert errlines[0].strip() == "[error] download failed: permission denied"

    out, err = r.runcommand("gin", "upload", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    assert len(errlines) == 1
    assert errlines[0].strip() == "[error] 1 operation failed"
    outlines = out.splitlines()
    assert outlines[-1].strip() == "upload failed: permission denied"

    # login to add key
    r.login()

    # set bad host key and check error
    with open(os.path.join(goodconfdir, "known_hosts"), "r+") as hostkeyfile:
        goodhostkey = hostkeyfile.read()
        badhostkey = goodhostkey.replace("AAA", "BBB")
        hostkeyfile.seek(0)
        hostkeyfile.write(badhostkey)

    # TODO: Check error messages
    out, err = r.runcommand("gin", "download", "--content", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    assert len(errlines) == 1
    assert errlines[0].strip() ==\
        "[error] download failed: server key does not match known host key"

    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    for line in errlines[:-1]:
        # TODO: Should print host key error
        assert line.strip().endswith("(content or server unavailable)")
    assert errlines[-1].strip() == "[error] 5 operations failed"

    out, err = r.runcommand("gin", "upload", exit=False)
    assert err, "Expected error, got nothing"
    errlines = err.splitlines()
    assert len(errlines) == 1
    assert errlines[0].strip() == "[error] 1 operation failed"
    outlines = out.splitlines()
    assert outlines[-1].strip() ==\
        "upload failed: server key does not match known host key"

    # login to fix key
    r.login()

    # Creating repository that already exists
    r.cdrel("..")

    out, err = r.runcommand("gin", "create", r.reponame, exit=False)
    assert err == ("[error] invalid repository name or "
                   "repository with the same name already exists")

    # Creating repository but local directory already exists (non-empty)
    anotherrepo = f"gin-test-{randint(0, 9999):04}"
    print(f"Creating directory '{anotherrepo}'")
    os.mkdir(anotherrepo)
    util.mkrandfile(os.path.join(anotherrepo, f"hold"), 20)

    out, err = r.runcommand("gin", "create", anotherrepo, exit=False)
    assert ("Creating repository" in out
            and "OK" in out), f"Failed to create {anotherrepo} on server"
    assert out.endswith(
        f"Repository download failed.\n'{anotherrepo}' already exists in the "
        "current directory and is not empty."
    )
    r.repositories[r.cmdloc] = anotherrepo
    assert err == "[error] 1 operation failed"

    out, err = r.runcommand("gin", "repos")
    assert anotherrepo in out

    print("DONE!")
