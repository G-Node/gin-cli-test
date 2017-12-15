loc=$(cd $(dirname $0) && pwd)
set -x
docker kill gintest
docker container rm gintest

rm -r "${loc}/gin-data"
