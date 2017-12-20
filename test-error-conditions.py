#!/usr/bin/env python
from random import randint
from runner import Runner


norepoerr = "ERROR This command must be run from inside a gin repository."

r = Runner()

r.login()
username = r.username

commands = [
    "upload",
    "download",
    "lock",
    "unlock",
    "get-content",
    "remove-content",
]

for cmd in commands:
    out, err = r.runcommand("gin", cmd, ".", exit=False)
    assert err == norepoerr, f"Unexpected error output {err}"


out, err = r.runcommand("gin", "lock", "foobar", exit=False)
assert err == norepoerr, f"Unexpected error output {err}"

# create repo (remote and local) and cd into directory
reponame = f"gin-test-{randint(0, 9999):04}"
repopath = f"{username}/{reponame}"
r.runcommand("gin", "create", reponame,
             "Test repository for error output -- Created with test scripts")
r.cdrel(reponame)

out, err = r.runcommand("gin", "lock", "foobar", exit=False)
assert out == "Error: No files matched foobar"
assert err == "ERROR 1 operation failed", f"Unexpected error output {err}"

r.cleanup(reponame)
r.logout()

print("DONE!")
