#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc

set -eu
source ./setenv.sh

gin logout
