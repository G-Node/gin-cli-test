#!/usr/bin/env python
import sys
import os
import subprocess as sp
import tempfile
from random import randint


loc = os.path.dirname(os.path.abspath(__file__))
env = {
    "PATH": os.environ.get("PATH"),
    "XDG_CONFIG_HOME": os.path.join(loc, "conf"),
    "XDG_CACHE_HOME": os.path.join(loc, "log"),
}
testroot = tempfile.TemporaryDirectory(prefix="gintest")
cmdloc = testroot.name


def runcommand(*args, inp=None, exit=True):
    print(f"> {' '.join(args)}")
    if inp:
        inp += "\n"
    p = sp.run(args, env=env, stdout=sp.PIPE, stderr=sp.PIPE, input=inp,
               cwd=cmdloc, encoding="utf-8")
    stdout, stderr = p.stdout.strip(), p.stderr.strip()
    if stdout:
        print(f"{stdout}")
    if stderr:
        print(f"E: {stderr}")
    if p.returncode and exit:
        sys.exit(p.returncode)
    return stdout, stderr


def cdrel(path):
    global cmdloc
    cmdloc = os.path.abspath(os.path.join(cmdloc, path))
    print(f"New dir: {cmdloc}")


username = "testuser"
password = "a test password 42"

norepoerr = "ERROR This command must be run from inside a gin repository."


out, err = runcommand("gin", "login", username, inp=password)


commands = [
    "upload",
    "download",
    "lock",
    "unlock",
    "get-content",
    "remove-content",
]

for cmd in commands:
    out, err = runcommand("gin", cmd, ".", exit=False)
    assert err == norepoerr, f"Unexpected error output {err}"


out, err = runcommand("gin", "lock", "foobar", exit=False)
assert err == norepoerr, f"Unexpected error output {err}"

# # create repo (remote and local) and cd into directory
reponame = f"gin-test-{randint(0, 9999):04}"
repopath = f"{username}/{reponame}"
runcommand("gin", "create", reponame,
           "Test repository for error output -- Created with test scripts")
cdrel(reponame)

out, err = runcommand("gin", "lock", "foobar", exit=False)
assert out == "Error: No files matched foobar"
assert err == "ERROR 1 operation failed", f"Unexpected error output {err}"

# create randfiles
# cleanup

runcommand("gin", "annex", "uninit")
runcommand("gin", "delete", repopath, inp=repopath)

runcommand("gin", "logout")

print("DONE!")
