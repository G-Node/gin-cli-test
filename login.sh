#!/usr/bin/env bash


source ./setenv.sh

gin login $username <<< $password

gin info
