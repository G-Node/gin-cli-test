#!/usr/bin/env bash

set -xeu

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

docker build --build-arg UID=${UID} -t ginclitests ginclitests
docker run --rm --network=ginbridge -v "${loc}/scripts/":/home/ginuser/scripts -v "${loc}/bin/":/ginbin --name gintestclient ginclitests
