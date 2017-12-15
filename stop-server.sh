loc=$(cd $(dirname $0) && pwd)
set -x

docker exec gintest rm -rv /data/ssh
docker kill gintest

rm -r "${loc}/gin-data"
