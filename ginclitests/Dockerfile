FROM base/archlinux

RUN pacman -Syu --noconfirm openssh git-annex python-pytest python-yaml gist

ARG UID=1000

RUN useradd -m -u $UID -s /bin/bash ginuser

USER ginuser

ENV PATH /ginbin:$PATH

# Requires scripts directory to be mounted under ginuser home
ENTRYPOINT ["/home/ginuser/scripts/run-all-tests.sh"]
