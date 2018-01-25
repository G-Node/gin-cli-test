#!/usr/bin/env bash

set -xeu

loc=$(cd $(dirname $0) && pwd)

./delete-all-test-repos.sh
./logout.sh

docker exec gintest rm -rfv /data/ssh
docker kill gintest

rm -r "${loc}/gin-data"
