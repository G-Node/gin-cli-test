FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common python-software-properties wget
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3.6
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.6 get-pip.py
RUN pip3.6 install pytest pyyaml

COPY ./git-annex-standalone-amd64.tar.gz /tmp/.
WORKDIR /tmp
RUN tar xf git-annex-standalone-amd64.tar.gz

ARG UID=1000
RUN useradd -m -u $UID -s /bin/bash ginuser
USER ginuser
ENV PATH /ginbin:/tmp/git-annex.linux:$PATH

WORKDIR "/home/ginuser"

# Requires scripts directory to be mounted under ginuser home
ENTRYPOINT ["/home/ginuser/scripts/run-all-tests.sh"]
