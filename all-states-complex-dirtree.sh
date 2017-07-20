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
repopath=${username}/${reponame}
gin create $reponame "Test repository --- Created with test scripts"
pushd $reponame

# create files in root
for idx in {000..050}
do
    fname=root-$idx.git
    echo "I am a root file, added to git" > $fname
    git add $fname
done
for idx in {070..090}
do
    fname=root-$idx.annex
    echo "I am a root file, added to annex" > $fname
    git annex add $fname
done

[ $(gin ls --short | grep -F "LC" | wc -l) -eq 72 ]

git commit -m "adding stuff"
[ $(gin ls --short | grep -F "LC" | wc -l) -eq 72 ]

git push
# git stuff pushed -- annex not synced
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 51 ]
[ $(gin ls --short | grep -F "LC" | wc -l) -eq 21 ]

gin upload
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 72 ]

# gin upload command should not have created an extra commit
[ $(git --no-pager log | grep "^commit" | wc -l) -eq 2 ]

# cleanup
git annex uninit
popd
rm -rf $repopath
gin delete $repopath <<< $repopath


echo "DONE!"
