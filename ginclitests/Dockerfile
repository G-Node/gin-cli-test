FROM base/archlinux

RUN pacman -Syu --noconfirm openssh git-annex python-pytest python-yaml

ENV PATH /ginbin:$PATH

ENTRYPOINT ["/scripts/run-all-tests.sh"]
