#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

set -xeu

# clean up old stuff from potentially improper server shutdown
docker network rm ginbridge || true
rm -fr "${loc}/gin-data" || true

docker pull gnode/ginhome

# copy init server data to live location
cp -a "./gin-data.init/." "./gin-data"

docker network create -d bridge ginbridge
docker run --rm --network=ginbridge -v "${loc}/gin-data/":/data -p 3000:3000 -p 2222:22 --name gintestserver -d gnode/ginhome
