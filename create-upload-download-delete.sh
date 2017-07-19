#!/usr/bin/env bash
# This script performs the following actions:
#  1. Log into gin (should use dev server)
#  2. Create a test repository
#  3. Create two random files in the test repository
#  4. Compute hashes for the new files
#  5. Upload the files
#  6. Delete the local copy of the repository
#  7. Perform a gin get, which performs a git clone and annex init, but does not download content
#  8. Check that the local random files are placeholders and have no content
#  9. Download the first file and check that only one file has content and correct md5 hash
# 10. Download the second file and check that both files have content and correct md5 hashes
# 11. Delete the local copy of the repository

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
fname2="file-${RANDOM}.rnd"
dd if=/dev/urandom of="$fname1" bs=1k count=2
dd if=/dev/urandom of="$fname2" bs=1k count=3

# save md5 hashes for checking later
md5sum * > "${testroot}/${reponame}.md5"

# upload files
gin upload

# delete local directory
git annex uninit
popd
rm -rf "$reponame"

# redownload and check the hashes
repopath=${username}/${reponame}
gin get $repopath
pushd $reponame

# both should be NC
[ $(gin ls --short | grep -F "NC" | wc -l ) -eq 2 ]
# both checksums should fail
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "FAILED" | wc -l ) -eq 2 ]

# download first file
gin download $fname1
# one file should be NC and the other OK
[ $(gin ls -s | grep -F "OK" | wc -l ) -eq 1 ]
[ $(gin ls --short | grep -F "NC" | wc -l ) -eq 1 ]
# one checksum should fail and one should succeed
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "OK" | wc -l ) -eq 1 ]
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "FAILED" | wc -l ) -eq 1 ]

# download everything
gin download .
# both files dhould be OK
[ $(gin ls -s | grep -F "OK" | wc -l ) -eq 2 ]
# both checksums should succeed
md5sum -c "${testroot}/${reponame}.md5"

# cleanup
git annex uninit
popd
rm -rf $reponame
gin delete $repopath <<< $repopath


echo "DONE!"
