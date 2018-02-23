#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc
./login.sh
./delete-all-test-repos.sh <<< echo
./logout.sh
