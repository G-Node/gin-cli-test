#!/usr/bin/env bash

loc=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
pushd $loc
source ./setenv.sh

gin login $username <<< $password

gin info
