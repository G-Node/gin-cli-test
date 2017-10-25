#!/usr/bin/env bash
# This script performs the following actions:
#  1. Log into gin (should use dev server)
#  2. Create a test repository
#  3. Create N random files in the test repository
#  4. Compute hashes for the new files
#  5. Upload the files
#  6. Make changes to some of the local files
#  7. Check that gin ls reports local changes correctly
#  8.

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

echo "FINISH ME"
false

# create randfiles
# cleanup
gin annex uninit
popd
rm -rf $repopath
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
