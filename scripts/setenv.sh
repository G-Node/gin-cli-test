#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1
}

export GIN_CONFIG_DIR=$loc/conf
export GIN_LOG_DIR=$loc/log

username=testuser
password="a test password 42"
