#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)
pushd $loc

set -xeu

docker exec gintestserver rm -rfv /data/ssh
docker kill gintestserver
docker network rm ginbridge

rm -r "${loc}/gin-data"

