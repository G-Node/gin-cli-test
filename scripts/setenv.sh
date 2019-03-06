#!/usr/bin/env bash

projectpath=$(git rev-parse --show-toplevel 2> /dev/null)
scriptsloc=${projectpath}/scripts

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1 2> /dev/urandom
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1 2> /dev/urandom
}


export GIN_CONFIG_DIR="$(mktemp -d)"
export GIN_LOG_DIR="${projectpath}/log"

defaultconf="${projectpath}/conf/config.yml"
mkdir -p ${GIN_CONFIG_DIR}
cp ${defaultconf} ${GIN_CONFIG_DIR}

username=testuser
password="a test password 42"
