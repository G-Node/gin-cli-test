#!/usr/bin/env python
from random import randint
from runner import Runner


username = "testuser"
password = "a test password 42"

norepoerr = "ERROR This command must be run from inside a gin repository."

r = Runner()

out, err = r.runcommand("gin", "login", username, inp=password)


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

# # create repo (remote and local) and cd into directory
reponame = f"gin-test-{randint(0, 9999):04}"
repopath = f"{username}/{reponame}"
r.runcommand("gin", "create", reponame,
             "Test repository for error output -- Created with test scripts")
r.cdrel(reponame)

out, err = r.runcommand("gin", "lock", "foobar", exit=False)
assert out == "Error: No files matched foobar"
assert err == "ERROR 1 operation failed", f"Unexpected error output {err}"

# create randfiles
# cleanup

r.runcommand("gin", "annex", "uninit")
r.runcommand("gin", "delete", repopath, inp=repopath)

r.runcommand("gin", "logout")

print("DONE!")
