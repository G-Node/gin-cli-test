#!/usr/bin/env bash

set -e
source ./setenv.sh

gin login $username <<< $password

# collect all test repo names
testrepos=$(gin repos | grep -oP "\w+/gin-test-(win-)?\d+")
echo "The following repositories will be deleted"
for reponame in $testrepos
do
    echo -e "\t $reponame"
    done
echo "Ctrl+C cancels"
read

# deleting
for reponame in $testrepos
do
    gin delete $reponame <<< $reponame
done

echo "DONE!"
