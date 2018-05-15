# Base system and dependencies for running the gin command line client tests
# See https://github.com/G-Node/gin-cli-test
FROM base/archlinux

RUN pacman -Syu --noconfirm openssh git-annex python-pytest python-yaml gist
RUN paccache -rk0
ENV PATH /ginbin:$PATH
