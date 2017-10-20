loc=$(cd $(dirname $0) && pwd)
docker run -v "${loc}/gin-data/":/data -v "${loc}":/root/tests --name gintest -d gnode/ginhome
