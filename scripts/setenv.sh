#!/usr/bin/env bash

scriptsloc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1 2> /dev/urandom
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1 2> /dev/urandom
}


export GIN_CONFIG_DIR="$(mktemp -d)"
export GIN_LOG_DIR="${scriptsloc}/../log"

defaultconf="${scriptsloc}/../conf/config.yml"
mkdir -p ${GIN_CONFIG_DIR}
cp ${defaultconf} ${GIN_CONFIG_DIR}

username=testuser
password="a test password 42"
