loc=$(cd $(dirname $0) && pwd)

mkgitfile() {
    dd if=/dev/urandom of=$1 bs=10k count=1
}

mkannexfile() {
    dd if=/dev/urandom of=$1 bs=100k count=1
}

export XDG_CONFIG_HOME=$loc/conf
export XDG_CACHE_HOME=$loc/log

username=testuser
password="a test password 42"
