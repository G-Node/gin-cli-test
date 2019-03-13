# GIN Client test scripts

## Repository layout

- [docker](./dockerfiles): Dockerfiles for test server and client.

Server directories:
- [gin-data.init](./gin-data.init): Initial configuration for GIN server.
    - Mount location: Is first copied to a temporary directory in `/tmp` and then mounted under `/data`.

Test directories:
- [conf](./conf): GIN client configuration directory.
- [log](./log): GIN client and test log directory.
- [scripts](./scripts): Integration tests written in Python.

The scripts in the root of the repository are for starting and stopping the server and running the test inside a client container.
- [start-server](./start-server): Makes two copies of `gin-data.init` in temporary directories, starts two gin@home server containers and creates a bridge network called `ginbridge`.
- [stop-server](./stop-server): Deletes the `gin-data.init` copies from the temporary directories, stops the server containers, and removes the `ginbridge`.
- [run-all-tests](./run-all-tests): Sets up the test client environment and runs all test scripts using `pytest`. Cleans up leftover repositories before exiting.
