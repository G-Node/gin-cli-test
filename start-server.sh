#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)
pushd $loc

set -xeu

docker pull gnode/ginhome

# copy init server data to live location
cp -a "./gin-data.init/." "./gin-data"

docker network create -d bridge ginbridge
docker run --rm --network=ginbridge -v "${loc}/gin-data/":/data -p 3000:3000 -p 2222:22 --name gintestserver -d gnode/ginhome
