#!/usr/bin/env bash

set -xeu

docker pull gnode/ginhome

loc=$(cd $(dirname $0) && pwd)

cp -a "${loc}/gin-data.init/." "${loc}/gin-data"

docker network create -d bridge ginbridge
docker run --rm --network=ginbridge -v "${loc}/gin-data/":/data -p 3000:3000 -p 2222:22 --name gintestserver -d gnode/ginhome
