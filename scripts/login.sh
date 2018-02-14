#!/usr/bin/env bash

loc=$(cd $(dirname $0) && pwd)
pushd $loc
source ./setenv.sh

gin login $username <<< $password

gin info
