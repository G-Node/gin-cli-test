#!/usr/bin/env bash

set -xeu
source ./setenv.sh

testroot="/tmp/gintest"
mkdir -p "$testroot"
cd "$testroot"

gin login $username <<< $password

# create repo (remote and local) and cd into directory
reponame=gin-test-${RANDOM}
repopath=${username}/${reponame}



mkdir ${reponame}-local-clone
pushd ${reponame}-local-clone

# create files in root
for idx in {0..50}
do
    fname=root-$idx.git
    mkgitfile $fname
done
for idx in {70..90}
do
    fname=root-$idx.annex
    mkannexfile $fname
done

# Create from local directory
gin create --here $reponame "Test repository --- Created with test scripts"
gin upload .
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 72 ]

# gin upload command should not have created an extra commit
[ $(gin git --no-pager log | grep "^commit" | wc -l) -eq 2 ]

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
    for jdx in {1..10}
    do
        fname=subfile-$jdx.annex
        mkannexfile $fname
    done
    popd
done

# Upload the files of the first subdirectory only and a couple from the second
gin upload subdir-a subdir-b/subfile-5.annex subdir-b/subfile-10.annex

# should only have 12 new synced files
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 84 ]
# there should be 56 untracked files total
[ $(gin ls --short | grep -F "??" | wc -l) -eq 54 ]
# can also check each directory individually
[ $(gin ls --short subdir-b | grep -F "??" | wc -l) -eq 8 ]
for idx in {c..f}
do
    dirname=subdir-$idx
    [ $(gin ls --short $dirname | grep -F "??" | wc -l) -eq 10 ]
done

# Unlock some files
gin unlock root-70.annex root-75.annex root-84.annex

# Unlocked files should be marked UL
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 3 ]

# Unlock a whole directory
gin unlock subdir-a
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 13 ]

# Check subdirectory only
[ $(gin ls --short subdir-a | grep -F "UL" | wc -l) -eq 10 ]

# Check again but from within the subdir
pushd subdir-a
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 10 ]
popd

# Relock one of the files
gin lock root-84.annex
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 12 ]

# check one of thee remaining unlocked files explicitly
[ $(gin ls --short root-70.annex | grep -F "UL" | wc -l) -eq 1 ]

# There should be no NC files so far
[ $(gin ls --short | grep -F "NC" | wc -l) -eq 0 ]

# drop some files and check the counts
gin rmc subdir-b/subfile-5.annex
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 1 ]

gin rmc subdir-b
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]

gin remove-content subdir-a
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]
[ $(gin ls --short subdir-a | grep -F "NC" | wc -l) -eq 10 ]
[ $(gin ls -s | grep -F "NC" | wc -l) -eq 12 ]

# NC files are broken symlinks
[ $(find -L . -type l   | wc -l) -eq 12 ]

# cleanup
gin annex uninit || true
popd
rm -rf $repopath
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
