# GIN Client test scripts

## Repository layout

- [docker](./dockerfiles): Dockerfiles for test server and client.

Server directories:
- [gin-data.init](./gin-data.init): Initial configuration for GIN server.
    - Mount location: Is first copied to a temporary directory in `/tmp` and then mounted under `/data`.

Client directories:
- [bin](./bin): Location of gin binary to use for the tests.
    - Mount location: `/ginbin`.
- [conf](./conf): GIN client configuration directory.
    - Mount location: `/home/ginuser/conf`
- [log](./log): GIN client and test log directory.
    - Mount location: `/home/ginuser/log`
- [scripts](./scripts): Integration tests written in Python. Directory gets mounted inside
    - Mount location: `/home/ginuser/scripts`

The scripts in the root of the repository are for starting and stopping the server and running the test inside a client container.
- [start-server](./start-server): Makes two copies of `gin-data.init` in `/tmp`, starts two gin@home server containers and creates a bridge network called `ginbridge`.
- [stop-server](./stop-server): Deletes the `gin-data.init` copies from `/tmp`, stops the server containers, and removes the `ginbridge`.
- [run-cont-tests](./run-cont-tests): Sets up the client container and runs all the tests under the `./scripts` directory. The output of the tests are written to a log file in `./log` alongside the GIN client log.
- [run-cont-tests-mv](./run-cont-tests-mv): Same as above but using the minimum supported version of `git-annex`.
- [run-cont](./run-cont): Sets up the client container and runs any command and arguments supplied after the script name.
- [run-cont-mv](./run-cont-mv): Same as above but using the minimum supported version of `git-annex`.
- [cont-shell](./cont-shell): Starts an interactive shell (bash) inside the client test container.
