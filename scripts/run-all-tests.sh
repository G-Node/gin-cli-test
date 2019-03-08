#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

if ! which gin
then
    echo "gin binary not found. Aborting"
    exit 1
fi

errorcount=0
errored=()

pytest -v
teststatus=$?

./delete-all-test-repos.sh <<< echo
./logout.sh

if [ $teststatus -gt 0 ]
then
    echo "Failed"
    exit 1
fi

echo "All tests completed successfully"
