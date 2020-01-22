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
    badaddress = "ssh://git@bad-hostname:22"
    r.runcommand("git", "remote", "set-url", name, badaddress)

    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"

    # count output lines with failed message
    outlines = out.splitlines()
    failmsg = "failed: authorisation failed or remote storage unavailable"
    nfail = len([ol for ol in outlines if failmsg in ol])
    assert nfail == 5
    assert err.strip().endswith("[error] 5 operations failed")

    # revert remote change
    r.runcommand("git", "remote", "set-url", name, address)

    # Change gin and git server address:port in config and test failures
    goodconfdir = r.env["GIN_CONFIG_DIR"]
    badconftemp = tempfile.TemporaryDirectory(prefix="badconf")
    badconfdir = os.path.join(badconftemp.name, "conf")
    r.env["GIN_CONFIG_DIR"] = badconfdir
    shutil.copytree(goodconfdir, badconfdir)
    with open(os.path.join(goodconfdir, "config.yml")) as conffile:
        confdata = yaml.load(conffile.read(), Loader=yaml.SafeLoader)

    confdata["servers"]["test"]["web"]["port"] = 1
    confdata["servers"]["test"]["git"]["port"] = 1
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

    # count output lines with failed message
    outlines = out.splitlines()
    failmsg = "failed: authorisation failed or remote storage unavailable"
    nfail = len([ol for ol in outlines if failmsg in ol])
    assert nfail == 5
    assert err.strip().endswith("[error] 5 operations failed")

    out, err = r.runcommand("gin", "download", exit=False)
    assert err, "Expected error, got nothing"
    assert err.strip() == "[error] download failed: permission denied"

    out, err = r.runcommand("gin", "upload", exit=False)
    assert err, "Expected error, got nothing"
    assert err.strip() == "[error] 1 operation failed"
    outlines = out.splitlines()
    assert outlines[-1].strip() == "upload failed: permission denied"

    # login to add key
    r.login()

    # set bad host key and check error
    with open(os.path.join(goodconfdir, "known_hosts"), "r+") as hostkeyfile:
        goodhostkey = hostkeyfile.read()
        badhostkey = goodhostkey.replace("A", "B")  # assumes at least one A
        hostkeyfile.seek(0)
        hostkeyfile.write(badhostkey)

    # TODO: Check error messages
    out, err = r.runcommand("gin", "download", "--content", exit=False)
    assert err, "Expected error, got nothing"
    assert err.strip() ==\
        "[error] download failed: server key does not match known host key"

    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"

    # count output lines with failed message
    outlines = out.splitlines()
    failmsg = "failed: authorisation failed or remote storage unavailable"
    nfail = len([ol for ol in outlines if failmsg in ol])
    assert nfail == 5
    assert err.strip().endswith("[error] 5 operations failed")

    out, err = r.runcommand("gin", "upload", exit=False)
    assert err, "Expected error, got nothing"
    assert err.strip() == "[error] 1 operation failed"
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


@pytest.fixture
def orunner():
    remoteloc = tempfile.TemporaryDirectory(prefix="gintest-remote")
    r = Runner(False)
    reponame = util.randrepo()
    os.mkdir(reponame)
    r.cdrel(reponame)
    r.runcommand("gin", "init")
    r.runcommand("gin", "add-remote", "--create", "--default",
                 "origin", f"dir:{remoteloc.name}")
    r.reponame = reponame
    r.repositories[r.cmdloc] = None

    r.runcommand("gin", "upload")

    r.cdrel("..")

    yield r

    r.cleanup()


@pytest.mark.offline
def test_errors_offline(orunner):
    r = orunner
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
    r.runcommand("git", "remote", "set-url", name, "#_not_a_real_path")

    out, err = r.runcommand("gin", "get-content", "datafiles", exit=False)
    assert err, "Expected error, got nothing"

    # count output lines with failed message
    outlines = out.splitlines()
    failmsg = "failed: authorisation failed or remote storage unavailable"
    nfail = len([ol for ol in outlines if failmsg in ol])
    assert nfail == 5
    assert err.strip().endswith("[error] 5 operations failed")

    print("DONE!")
