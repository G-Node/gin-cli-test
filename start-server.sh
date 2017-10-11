loc=$(cd $(dirname $0) && pwd)
docker run -v "${loc}/gin-data/":/data -p 3000:3000 -p 2222:22 --name gintest -d gnode/ginhome
