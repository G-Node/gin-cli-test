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

loc=$(cd $(dirname $0) && pwd)
pushd $loc

set -xeu
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

# delete local directory
gin annex uninit || true
popd
rm -rf "$reponame"

# redownload and check the hashes
repopath=${username}/${reponame}
gin get $repopath
pushd $reponame

# both should be NC
[ $(gin ls --short | fgrep "NC" | wc -l ) -eq 2 ]
# shoud have 2 broken links
[ $(find -L . -type l | wc -l) -eq 2 ]


# download first file
gin get-content $fname1
# one file should be NC and the other OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 1 ]
[ $(gin ls --short | fgrep "NC" | wc -l ) -eq 1 ]
# one checksum should fail and one should succeed
[ $(md5sum -c "${testroot}/${reponame}.md5" | fgrep "OK" | wc -l ) -eq 1 ]
[ $(find -L . -type l | wc -l) -eq 1 ]

# download everything
gin get-content .
# both files should be OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 2 ]
# both checksums should succeed
md5sum -c "${testroot}/${reponame}.md5"

# cleanup
gin annex uninit || true
popd
rm -rf $reponame
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
