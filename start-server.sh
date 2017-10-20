loc=$(cd $(dirname $0) && pwd)
set -x
docker run -v "${loc}/gin-data/":/data -v "${loc}":/root/tests --name gintest -d gnode/ginhome
