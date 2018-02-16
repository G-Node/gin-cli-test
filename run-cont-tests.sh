#!/usr/bin/env bash

set -eu

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

docker build --build-arg UID=${UID} -t ginclitests ginclitests

source ./scripts/setenv.sh
testlog=${GIN_LOG_DIR}/tests.log
echo "Running tests and logging to ${testlog}"
echo $(pwd)
docker run --rm --network=ginbridge -v "${loc}/scripts/":/home/ginuser/scripts -v "${loc}/bin/":/ginbin --name gintestclient ginclitests &> ${testlog}
