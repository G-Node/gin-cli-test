#!/usr/bin/env bash

set -xeu

loc=$(cd $(dirname $0) && pwd)

docker build -t ginclitests ginclitests
docker run --rm --network=ginbridge -v "${loc}/scripts/":/scripts -v "${loc}/bin/":/ginbin --name gintestclient ginclitests
