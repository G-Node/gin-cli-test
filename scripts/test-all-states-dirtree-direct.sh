#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

echo "****** Running ${BASH_SOURCE[0]} ******"

set -xeu
source ./setenv.sh

testroot="/tmp/gintest"
mkdir -p "$testroot"
cd "$testroot"

gin login $username <<< $password

# create repo (remote and local) and cd into directory
reponame=gin-test-${RANDOM}
repopath=${username}/${reponame}
gin create $reponame "Test repository --- all states direct mode"
pushd $reponame

echo "************ SWITCHING TO DIRECT MODE ************"
gin annex direct

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

[ $(gin ls --short | grep -F "??" | wc -l) -eq 72 ]

gin commit root*
[ $(gin ls --short | grep -F "LC" | wc -l) -eq 21 ]

# git files in direct mode can't be in LC state
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 51 ]

gin upload  # since we manually did the commit, the upload should sync everything
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 72 ]

# gin upload command should not have created an extra commit
[ $(gin git --no-pager log | grep "^commit" | wc -l) -eq 2 ]

# Create more root files that will remain UNTRACKED
for idx in {a..f}
do
    fname=root-file-$idx.untracked
    echo "I am a root file. I will not be added to git or annex" > $fname
done

# modify all tracked files
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

[ $(gin ls --short | grep -F "MD" | wc -l) -eq 72 ]

gin upload *.annex *.git  # upload all except .untracked
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 72 ]

# should have 3 commits so far
[ $(gin git --no-pager log | grep "^commit" | wc -l) -eq 3 ]

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
# there should be 54 untracked files total
[ $(gin ls --short | grep -F "??" | wc -l) -eq 54 ]
# can also check each directory individually
[ $(gin ls --short subdir-b | grep -F "??" | wc -l) -eq 8 ]
for idx in {c..f}
do
    dirname=subdir-$idx
    [ $(gin ls --short $dirname | grep -F "??" | wc -l) -eq 10 ]
done

# Unlocking should be noop in direct mode
gin unlock root-70.annex root-75.annex root-84.annex

[ $(gin ls --short | grep -F "UL" | wc -l) -eq 0 ]
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 84 ]

gin unlock subdir-a
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 0 ]
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 84 ]

# Lock too
gin lock root-84.annex
[ $(gin ls --short | grep -F "UL" | wc -l) -eq 0 ]
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 84 ]

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

if [ "$(gin git config --local core.symlinks)" != "false" ]
then
    # NC files are broken symlinks
    [ $(find -L . -type l | wc -l) -eq 12 ]
else
    # NC files are pointer files to annex
    [ $(grep -F "git/annex/objects" -r . | wc -l) -eq 12 ]
fi

# push everything and then rmc it
gin upload .
gin rmc .

# annex files are now NC
[ $(gin ls --short | grep -F "NC" | wc -l) -eq 81 ]

# git files are still OK (untracked were added too)
[ $(gin ls --short | grep -F "OK" | wc -l) -eq 57 ]


# remove a few files and check their status
rm -v subdir-a/subfile-1.annex
rm -v root-10.git
rm -rv subdir-b
[ $(gin ls --short | grep -F "RM" | wc -l) -eq 12 ]

gin commit .
[ $(gin ls --short | grep -F "RM" | wc -l) -eq 0 ]

# add new files, remove some existing ones, check status and upload
mkannexfile "new-annex-file"
mkgitfile "new-git-file"
rm -r subdir-c
[ $(gin ls --short | grep -F "RM" | wc -l) -eq 10 ]
[ $(gin ls --short | grep -F "??" | wc -l) -eq 2 ]

gin upload .
[ $(gin ls --short | grep -F "RM" | wc -l) -eq 0 ]
[ $(gin ls --short | grep -F "??" | wc -l) -eq 0 ]

# cleanup
gin annex uninit || true
popd
rm -rf $repopath
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
