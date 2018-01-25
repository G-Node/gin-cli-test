#!/usr/bin/env bash

set -eu
source ./setenv.sh

gin login $username <<< $password

# collect all test repo names
testrepos=$(gin repos | grep -o "\w\+/gin-test-\(win-\)\?[0-9]\+" | sort -u)
if [[ "$testrepos" != "" ]]
then
    echo "The following repositories will be deleted"
    for reponame in $testrepos
    do
        echo -e "\t $reponame"
    done
    echo "Ctrl+C cancels"
    read
else
    echo "No test repos on server"
fi

# deleting
for reponame in $testrepos
do
    gin delete $reponame <<< $reponame
done

repostore="./gin-data/gogs-repositories/$username/"
if compgen -G "$repostore/gin-test-*" > /dev/null
then
    testrepos="$repostore/gin-test-*"
    echo "Deleting leftover files in the following directories"
    for dirname in $testrepos
    do
        echo -e "\t $dirname"
    done
    echo "Ctrl+C cancels"
    read

    # chmod and delete
    for reponame in $testrepos
    do
        chmod 777 -R $reponame
        rm -r $reponame
        echo "Removed $reponame"
    done
fi

echo "DONE!"
