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


# create local config file which sets filesize threshold to 0kb
echo -e "annex:\n    minsize: 0kB" > config.yml

# gitfile should be added to annex now
mkgitfile smallfile
gin upload smallfile

# should be symlink
[ -L smallfile ]

# .md file should still be excluded from the global config file
mkgitfile anotherfile.md
gin upload anotherfile.md

# should not be a symlink
[ ! -L anotherfile.md ]

# cleanup
gin annex uninit || true
popd
rm -rf $repopath
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
