#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)
pushd $loc

set -eu
source ./setenv.sh

gin logout
rm GIN_CONFIG_DIR=${loc}/conf/ginhostkey  # TODO: Remove when gin does this automatically
