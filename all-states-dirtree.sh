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
    echo "I am root file $idx, added to git" > $fname
    git add $fname
done
for idx in {070..090}
do
    fname=root-$idx.annex
    echo "I am root file $idx, added to annex" > $fname
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
        echo "I am file $jdx in directory $dirname" > $fname
    done
    popd
done

# Upload the files of the first subdirectory only and a couple from the second
gin upload subdir-a subdir-b/subfile-05.annex subdir-b/subfile-10.annex

# should only have 10 new synced files
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
gin unlock root-070.annex root-075.annex root-084.annex

# Unlocked files should be marked UL
[ $(gin ls --short subdir-b | grep -F "UL" | wc -l) -eq 3 ]

# Relock one of the files
gin lock root-084.annex
[ $(gin ls --short subdir-b | grep -F "UL" | wc -l) -eq 2 ]

# There should be no NC files so far
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 0 ]

# drop some files and check the counts
gin rmc subdir-b/subfile-05.annex
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 1 ]

gin rmc subdir-b
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]

gin remove-content subdir-a
[ $(gin ls --short subdir-b | grep -F "NC" | wc -l) -eq 2 ]
[ $(gin ls --short subdir-a | grep -F "NC" | wc -l) -eq 10 ]
[ $(gin ls -s | grep -F "NC" | wc -l) -eq 12 ]

# NC files are broken symlinks
[ $(find . -xtype l | wc -l) -eq 12 ]

# cleanup
git annex uninit || true
popd
rm -rf $repopath
gin delete $repopath <<< $repopath


echo "DONE!"
