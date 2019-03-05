#!/usr/bin/env bash
#
# Upload and download larger files and observe output.
# This isn't really a test and requires human eyeballs.

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

echo "****** Running ${BASH_SOURCE[0]} ******"

set -euo pipefail
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


# make a lot of git files and upload them
echo "Creating files "
for idx in {0..4000}
do
    # not using mkgitfile to create 40k files
    dd if=/dev/urandom of=gitfile-${idx} bs=40k count=1 status=none
    echo -ne " ${idx}\r"
done
echo "Done"

echo "gin commit ..."
gin commit gitfile-*
echo "======================"

echo "gin upload ..."
gin upload gitfile-*
echo "======================"

# git log -n1

echo "======================"

# gin ls

echo "======================"

echo "Cleaning up"
# cleanup
gin annex uninit || true
popd
rm -rf $reponame
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
