loc=$(cd $(dirname $0) && pwd)
docker run -v "${loc}/gin-data/":/data -v "${loc}":/root/tests -p 3000:3000 -p 2222:22 --name gintest -d gnode/ginhome
