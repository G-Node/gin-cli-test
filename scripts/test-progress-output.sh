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

gin --version

gin login $username <<< $password

progtests() {
    echo "#################################################"
    outflag=""
    if (( $# > 0 )); then
        outflag=$1
        echo "Using ${outflag} for supported commands"
    else
        echo "Running without flag"
    fi

    # create repo (remote and local) and cd into directory
    reponame=gin-test-${RANDOM}
    gin create $reponame "Test repository --- Created with test scripts"
    pushd $reponame

    # create randfiles
    for idx in {00..11}; do
        fname="file-${idx}.rnd"
        echo "Creating $fname"
        dd if=/dev/urandom of=$fname bs=3M count=20 2> /dev/null
    done

    # upload files
    echo ">>> gin upload"
    gin upload ${outflag} .
    echo "<<<"

    # make some git files and upload them
    for idx in {1..4}
    do
        mkgitfile gitfile-$idx
    done
    gin upload ${outflag} gitfile-*

    # delete local directory
    gin annex uninit || true
    popd
    rm -rf "$reponame"

    # redownload
    repopath=${username}/${reponame}
    echo ">>> gin get"
    gin get ${outflag} $repopath
    pushd $reponame

    # download first file
    echo ">>> gin get-content file-00.rnd"
    gin get-content ${outflag} file-00.rnd
    echo "<<<"

    # download everything
    echo ">>> gin get-content"
    gin get-content ${outflag} .
    echo "<<<"
    # all files should be OK
    [ $(gin ls -s | fgrep "OK" | wc -l ) -eq 16 ]

    # modify one annex and one git file
    echo "Mofifying gitfile-4"
    mkgitfile gitfile-4
    echo "Modifying file-00.rnd"
    gin unlock ${outflag} file-00.rnd
    mkannexfile file-00.rnd

    # upload again
    gin upload ${outflag} .

    # unlock everything
    gin unlock ${outflag} .

    # lock some
    gin lock ${outflag} file-{00..05}.rnd

    # upload all
    gin upload ${outflag} .

    # modify and commit
    gin unlock ${outflag} .
    for idx in {05..11}; do
        fname="file-${idx}.rnd"
        echo "Modifying $fname"
        dd if=/dev/urandom of=$fname bs=3M count=20 2> /dev/null
    done
    gin upload ${outflag} .

    # delete local again
    gin annex uninit || true
    popd
    rm -rf "$reponame"

    # once more using download command
    echo ">>> gin get"
    gin get ${outflag} $repopath
    pushd $reponame

    # do a gin download without content
    echo ">>> gin download"
    gin download ${outflag}
    echo "<<<"

    # now get all content
    echo ">>> gin download ${outflag} --content"
    gin download ${outflag} --content
    echo "<<<"

    # all files should be OK
    [ $(gin ls -s | fgrep "OK" | wc -l ) -eq 16 ]

    # delete a couple of files and check output message
    rm gitfile-4
    rm gitfile-1
    rm file-00.rnd
    gin upload ${outflag} .

    # cleanup
    gin annex uninit || true
    popd
    rm -rf $reponame
    gin delete $repopath <<< $repopath

}

progtests "--verbose"
progtests "--json"
progtests

gin logout

echo "DONE!"
