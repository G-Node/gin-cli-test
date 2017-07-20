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

# Create more root files that will remain UNTRACKED
for idx in {a..f}
do
    fname=root-file-$idx.untracked
    echo "I am a root file. I will not be added to git or annex" > $fname
done

# Create some subdirectories with files
for idx in {a..f}
do
    dirname=subdir-$idx
    mkdir -v $dirname
    pushd $dirname
    for jdx in {01..10}
    do
        fname=subfile-$jdx.annex
        echo "I am a file in directory $dirname" > $fname
    done
done

# Upload the files of the first subdirectory only
gin upload subdir-a

# should only have 10 new synced files
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 82 ]


# cleanup
git annex uninit
popd
rm -rf $repopath
gin delete $repopath <<< $repopath


echo "DONE!"
