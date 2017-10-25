#!/usr/bin/env bash
# This script performs the following actions:
#  1. Log into gin (should use dev server)
#  2. Create a test repository
#  3. Create two random files in the test repository
#  4. Compute hashes for the new files
#  5. Upload the files
#  6. Create three files with extensions .md and .py (source code)
#  7. Upload the files
#  8. Check that the random files are in annex and the source code files are in git
#  9. Delete the local copy of the repository
#  10. Perform a gin get, which performs a git clone and annex init, but does not download content
#  11. Check that the random files are in annex and the source code files are in git
#  12. Check that the local random files are placeholders and have no content
#  13. Download the first file and check that only one file has content and correct md5 hash
#  14. Download the second file and check that both files have content and correct md5 hashes
#  15. Delete the local copy of the repository

set -x
set -e


source ./setenv.sh

testroot="/tmp/gintest"
mkdir -p "$testroot"
cd "$testroot"

gin login $username <<< $password

# create repo (remote and local) and cd into directory
reponame=gin-test-${RANDOM}
gin create $reponame "Test repository --- Created with test scripts"
pushd $reponame

# create randfiles
fname1="file-${RANDOM}.rnd"
mkannexfile $fname1
fname2="file-${RANDOM}.rnd"
mkannexfile $fname2

# save md5 hashes for checking later
md5sum * > "${testroot}/${reponame}.md5"

# upload files
gin upload .

# create source files
echo "I am a markdown file" > markdown.md
echo "I am a python script" > python.py

# upload files
gin upload .

# create a 'foo' file (custom extension found in config file)
echo "I am a foo file" > biscuits.foo

# upload foo file
gin upload biscuits.foo

# create a py file that (for some reason) is larger than the configured annex threshold
# this should be added to git because it matches the pattern even though it's larger than the threshold
mkannexfile bigscript.py
gin upload .

# delete local directory
gin annex uninit || true
popd
rm -rf "$reponame"

# redownload and check the hashes
repopath=${username}/${reponame}
gin get $repopath
pushd $reponame

# git files should be here
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 4 ]

# both rand files should be NC
[ $(gin ls --short | fgrep "NC" | wc -l ) -eq 2 ]
# both checksums should fail; md5sum should warn about missing files because of broken links
[ $(md5sum -c "${testroot}/${reponame}.md5" | fgrep "FAILED" | wc -l ) -eq 2 ]

# download first rand file
gin get-content $fname1
# one file should be NC and the rest OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 5 ]
[ $(gin ls --short | fgrep "NC" | wc -l ) -eq 1 ]
# one checksum should fail and one should succeed
[ $(md5sum -c "${testroot}/${reponame}.md5" | fgrep "OK" | wc -l ) -eq 1 ]
[ $(md5sum -c "${testroot}/${reponame}.md5" | fgrep "FAILED" | wc -l ) -eq 1 ]

# download everything
gin get-content .
# both files should be OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 6 ]
# both checksums should succeed
md5sum -c "${testroot}/${reponame}.md5"

# cleanup
gin annex uninit || true
popd
rm -rf $reponame
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
