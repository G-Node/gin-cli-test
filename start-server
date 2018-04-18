#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

set -xeu

# clean up old stuff from potentially improper server shutdown
docker network rm ginbridge || true

docker pull gnode/ginhome

# copy init server data to live location
srvdata="/tmp/gin-data-${RANDOM}"
cp -a "./gin-data.init/." "${srvdata}"

docker network create -d bridge ginbridge
docker run --rm --network=ginbridge -v "${srvdata}":/data -p 3000:3000 -p 2222:22 --name gintestserver -d gnode/ginhome
