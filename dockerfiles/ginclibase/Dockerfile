# Base system and dependencies for running the gin command line client tests
# See https://github.com/G-Node/gin-cli-test
FROM archlinux/base

RUN pacman -Syu --noconfirm openssh git-annex python-pytest python-pytest-xdist python-pytest-forked python-yaml gist pacman-contrib
RUN paccache -rk0
ENV PATH /ginbin:$PATH
