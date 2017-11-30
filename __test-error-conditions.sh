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
