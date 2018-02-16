#!/usr/bin/env bash
#
# Use this script to start the test runner container in the background and execute any command that is supplied as an argument.
# The container is killed at the end of the run.
# The script blindly passes whatever arguments are supplied to the container as a command, so proper command syntax and paths are required.

cmd=$*

set -eu

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

docker build --build-arg UID=${UID} -t ginclitests dockerfiles/tester
docker run --rm --network=ginbridge -v "${loc}/testuserhome":/home/ginuser -v "${loc}/scripts/":/home/ginuser/scripts -v "${loc}/bin/":/ginbin -i --name gintestclient -d ginclitests

set +e
docker exec gintestclient $cmd
cmdstat=$?

docker kill gintestclient

exit ${cmdstat}
