#!/usr/bin/env bash

set -xeu

loc=$(cd $(dirname $0) && pwd)

docker exec gintestserver rm -rfv /data/ssh
docker kill gintestserver
docker network rm ginbridge

rm -r "${loc}/gin-data"

