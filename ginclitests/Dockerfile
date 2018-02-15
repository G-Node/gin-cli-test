FROM base/archlinux

RUN pacman -Syu --noconfirm openssh git-annex python-pytest python-yaml
RUN useradd -ms /bin/bash ginuser

USER ginuser

ENV PATH /ginbin:$PATH

ENTRYPOINT ["/scripts/run-all-tests.sh"]
