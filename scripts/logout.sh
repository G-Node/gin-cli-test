#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)

set -eu
source ${loc}/setenv.sh

gin logout
rm GIN_CONFIG_DIR=$loc/conf/ginhostkey  # TODO: Remove when gin does this automatically
