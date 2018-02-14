#!/usr/bin/env bash
#
# Upload and download larger files and observe output.
# This isn't really a test and requires human eyeballs.

loc=$(cd $(dirname $0) && pwd)
pushd $loc

set -xeu
source ./setenv.sh

testroot="/tmp/gintest"
mkdir -p "$testroot"
cd "$testroot"

gin login $username <<< $password

# create repo (remote and local) and cd into directory
reponame=gin-test-${RANDOM}
gin create $reponame "Test repository --- Created with test scripts"
pushd $reponame

# create randfiles
fname1="file-${RANDOM}.rnd"
echo "Creating $fname1"
dd if=/dev/urandom of=$fname1 bs=3M count=20 2> /dev/null
fname2="file-${RANDOM}.rnd"
echo "Creating $fname2"
dd if=/dev/urandom of=$fname2 bs=3M count=30 2> /dev/null
fname3="file-${RANDOM}.rnd"
echo "Creating $fname3"
dd if=/dev/urandom of=$fname3 bs=1M count=30 2> /dev/null

# upload files
echo ">>> gin upload"
gin upload .
echo "<<<"

# make some git files and upload them
for idx in {1..4}
do
    mkgitfile gitfile-$idx
done
gin upload gitfile-*

# delete local directory
gin annex uninit || true
popd
rm -rf "$reponame"

# redownload and check the hashes
repopath=${username}/${reponame}
echo ">>> gin get"
gin get $repopath
pushd $reponame

# download first file
echo ">>> gin get-content"
gin get-content $fname1
echo "<<<"

# download everything
echo ">>> gin get-content"
gin get-content .
echo "<<<"
# all files should be OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 7 ]

# modify one annex and one git file
echo "Mofifying gitfile-4"
mkgitfile gitfile-4
echo "Modifying $fname1"
gin unlock $fname1
mkannexfile $fname1

# upload again
gin upload .

# delete local again
gin annex uninit || true
popd
rm -rf "$reponame"

# once more using download command
echo ">>> gin get"
gin get $repopath
pushd $reponame

# do a gin download without content
echo ">>> gin download"
gin download
echo "<<<"

# now get all content
echo ">>> gin download --content"
gin download --content
echo "<<<"

# all files should be OK
[ $(gin ls -s | fgrep "OK" | wc -l ) -eq 7 ]

# delete a couple of files and check output message
rm gitfile-4
rm gitfile-1
rm $fname1
gin upload .

# cleanup
gin annex uninit || true
popd
rm -rf $reponame
gin delete $repopath <<< $repopath

gin logout

echo "DONE!"
