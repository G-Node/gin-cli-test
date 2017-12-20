#!/usr/bin/env bash

set -x
set -e


source ./setenv.sh

testroot="/tmp/gintest"
mkdir -p "$testroot"
cd "$testroot"

norepoerr="ERROR This command must be run from inside a gin repository." 

gin login $username <<< $password

err=$(gin upload . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin download . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin lock . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin unlock . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin get-content . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin remove-content . 2>&1) || true
[ "$err" == "$norepoerr" ]

err=$(gin lock foobar 2>&1) || true
[ "$err" == "$norepoerr" ]

# create repo (remote and local) and cd into directory
reponame=gin-test-${RANDOM}
gin create $reponame "Test repository for errors --- Created with test scripts"
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
