#!/usr/bin/env bash

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
[ $(gin ls | grep -F "NC" | wc -l ) -eq 2 ]
# both checksums should fail
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "FAILED" | wc -l ) -eq 2 ]

# download first file
gin download $fname1
# one file should be NC and the other OK
[ $(gin ls | grep -F "OK" | wc -l ) -eq 1 ]
[ $(gin ls | grep -F "NC" | wc -l ) -eq 1 ]
# one checksum should fail and one should succeed
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "OK" | wc -l ) -eq 1 ]
[ $(md5sum -c "${testroot}/${reponame}.md5" | grep -F "FAILED" | wc -l ) -eq 1 ]

# download everything
gin download .
# both files dhould be OK
[ $(gin ls | grep -F "OK" | wc -l ) -eq 2 ]
# both checksums should succeed
md5sum -c "${testroot}/${reponame}.md5"

# cleanup
git annex uninit
popd
rm -rf $repopath
gin delete $repopath <<< $repopath


echo "DONE!"
