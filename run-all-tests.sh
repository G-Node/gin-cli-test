loc=$(cd $(dirname $0) && pwd)
cd $loc

errorcount=0
errored=()

for testscript in test-*.sh
do
    ./$testscript
    teststatus=$?
    if [ $teststatus -ne 0 ]
    then
        echo "Test $testscript failed"
        errorcount=$((errorcount+1))
        errored+=("$testscript")
    fi
done

./delete-all-test-repos.sh <<< echo
./logout.sh

if [ $errorcount -gt 0 ]
then
    echo "------------"
    echo "Tests failed"
    echo "------------"
    for testscript in "${errored[@]}"
    do
        echo $testscript
    done
    exit 1
fi

echo "All tests succeeded"
