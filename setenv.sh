#!/usr/bin/env bash

set -xeu

loc=$(cd $(dirname $0) && pwd)

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1
}

export GIN_CONFIG=$loc/conf/g-node/gin/config.yml
export GIN_LOG=$loc/log/gin/gin.log

username=testuser
password="a test password 42"
