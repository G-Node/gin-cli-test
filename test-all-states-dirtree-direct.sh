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

echo "************ SWITCHING TO DIRECT MODE ************"
gin annex direct

# create files in root to be annexed
for idx in {70..90}
do
    fname=root-$idx.annex
    mkannexfile $fname
done

[ $(gin ls --short | grep -F "??" | wc -l) -eq 21 ]

gin upload .
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 21 ]


# modify them
for idx in {70..90}
do
    fname=root-$idx.annex
    mkannexfile $fname
done

[ $(gin ls --short | grep -F "MD" | wc -l) -eq 21 ]

gin upload .

# should have 3 commits so far
[ $(gin git --no-pager log | grep "^commit" | wc -l) -eq 3 ]

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
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 33 ]
# there should be 54 untracked files total
[ $(gin ls --short | grep -F "??" | wc -l) -eq 54 ]
# can also check each directory individually
[ $(gin ls --short subdir-b | grep -F "??" | wc -l) -eq 8 ]
for idx in {c..f}
do
    dirname=subdir-$idx
    [ $(gin ls --short $dirname | grep -F "??" | wc -l) -eq 10 ]
done

# There should be no NC files so far
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 0 ]

# drop some files and check the counts
gin rmc subdir-b/subfile-5.annex
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 1 ]

gin rmc subdir-b
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]

gin remove-content subdir-a
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]
[ $(gin ls --short subdir-a | grep -F "NC" | wc -l) -eq 10 ]
[ $(gin ls -s | grep -F "NC" | wc -l) -eq 12 ]

[ $(gin ls --short | grep -F "OK" | wc -l) -eq 21 ]

# Create some small files that should be added to git (not annex)
mkdir -v files-for-git
pushd files-for-git
for idx in {1..5}
do
    fname=subfile-$idx.git
    mkgitfile $fname
done
popd

gin upload files-for-git
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 26 ]

# none of these files should be in annex
[ $(gin annex status files-for-git | wc -l) -eq 0 ]

if [ "$(gin git config --local core.symlinks)" != "false" ]
then
    # NC files are broken symlinks
    [ $(find -L . -type l | wc -l) -eq 12 ]
else
    # NC files are pointer files to annex
    [ $(grep -F "git/annex/objects" -r . | wc -l) -eq 12 ]
fi

# modify 2 git files and check their status
mkgitfile files-for-git/subfile-3.git
mkgitfile files-for-git/subfile-2.git
[ $(gin ls --short files-for-git | grep -F "LC" | wc -l) -eq 2 ]

# cleanup
gin annex uninit || true
popd
rm -rf $repopath
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
