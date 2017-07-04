#!/usr/bin/env bash

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
dd if=/dev/urandom of="$fname1" bs=10M count=1
dd if=/dev/urandom of="$fname2" bs=10M count=2

# save md5 hashes for checking later
md5sum * > "${testroot}/${reponame}.md5"

# upload files
gin upload

# delete local directory
popd
chmod 777 -R "$reponame"
rm -r "$reponame"

# redownload and check the hashes
gin get $username/$reponame
pushd $reponame
md5sum -c "${testroot}/${reponame}.md5"

# cleanup
popd
chmod 777 -R "$reponame"
rm -r "$reponame"
