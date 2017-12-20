#!/usr/bin/env python
import os
from runner import Runner
import util


r = Runner()
r.login()
username = r.username

# create repo (remote and local) and cd into directory
reponame = util.randrepo()
repopath = f"{username}/{reponame}"

localdir = f"{reponame}-local-clone"
os.mkdir(localdir)
r.cdrel(localdir)

# create files in root
for idx in range(51):
    util.mkrandfile(f"root-{idx}.git", 1)
for idx in range(70, 91):
    util.mkrandfile(f"root-{idx}.annex", 100)

# Create from local directory
r.runcommand("gin", "create", "--here", reponame,
             "Test repository for create --here --- Created with test script")
r.runcommand("gin", "upload", ".")

out, err = r.runcommand("gin", "ls", "--short")
synced = sum(1 for line in out.splitlines() if line.startswith("OK"))
assert synced == 72, f"Expected 72 files, got {synced}"

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

# Upload the files of the first subdirectory only and a couple from the second
r.runcommand("gin", "upload", "subdir-a", "subdir-b/subfile-5.annex",
             "subdir-b/subfile-10.annex")


def lscount(*paths, fltr=""):
    out, err = r.runcommand("gin", "ls", "--short", *paths)
    return sum(1 for line in out.splitlines() if line.startswith(fltr))


# should only have 12 new synced files
synced = lscount(fltr="OK")
assert synced == 84, f"Expected 84 files, got {synced}"
# there should be 54 untracked files total
untracked = lscount(fltr="??")
assert untracked == 54, f"Expected 54 files, got {untracked}"
# can also check each directory individually
untracked = lscount("subdir-b", fltr="??")
assert untracked == 8, f"Expected 8 files, got {untracked}"
for c in "cdef":
    untracked = lscount(f"subdir-{c}", fltr="??")
    assert untracked == 10, f"Expected 10 files, got {untracked}"

# # Unlock some files
r.runcommand("gin", "unlock", "root-70.annex",
             "root-75.annex", "root-84.annex")

# # Unlocked files should be marked UL
# [ $(gin ls --short | grep -F "UL" | wc -l) -eq 3 ]
r.runcommand("gin", "ls", "--short")


# # Unlock a whole directory
# gin unlock subdir-a
# [ $(gin ls --short | grep -F "UL" | wc -l) -eq 13 ]

# # Check subdirectory only
# [ $(gin ls --short subdir-a | grep -F "UL" | wc -l) -eq 10 ]

# # Check again but from within the subdir
# pushd subdir-a
# [ $(gin ls --short | grep -F "UL" | wc -l) -eq 10 ]
# popd

# # Relock one of the files
# gin lock root-84.annex
# [ $(gin ls --short | grep -F "UL" | wc -l) -eq 12 ]

# # check one of thee remaining unlocked files explicitly
# [ $(gin ls --short root-70.annex | grep -F "UL" | wc -l) -eq 1 ]

# # There should be no NC files so far
# [ $(gin ls --short | grep -F "NC" | wc -l) -eq 0 ]

# # drop some files and check the counts
# gin rmc subdir-b/subfile-5.annex
# [ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 1 ]

# gin rmc subdir-b
# [ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]

# gin remove-content subdir-a
# [ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]
# [ $(gin ls --short subdir-a | grep -F "NC" | wc -l) -eq 10 ]
# [ $(gin ls -s | grep -F "NC" | wc -l) -eq 12 ]

# # NC files are broken symlinks
# [ $(find -L . -type l   | wc -l) -eq 12 ]

# cleanup
r.cleanup(reponame)
r.logout()

print("Done!")
