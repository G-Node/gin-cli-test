# Set up user for running test scripts from https://github.com/G-Node/gin-cli-test
FROM achkts/ginclitests
ARG UID=1000
RUN useradd -m -u $UID -s /bin/bash ginuser
USER ginuser

# Requires scripts directory to be mounted under ginuser home
ENTRYPOINT ["/home/ginuser/scripts/run-all-tests.sh"]
