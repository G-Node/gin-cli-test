#!/usr/bin/env bash

scriptsloc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1
}

testroot=${scriptsloc}/..
export GIN_CONFIG_DIR=${testroot}/testuserhome/conf
export GIN_LOG_DIR=${testroot}/testuserhome/log

username=testuser
password="a test password 42"
