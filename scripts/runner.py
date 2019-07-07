import sys
import os
import subprocess as sp
import tempfile
import util


TESTCONFIG = """
annex:
  exclude:
  - '*.foo'
  - '*.md'
  - '*.py'
  minsize: 50kB
"""


class Runner(object):

    username = "testuser"
    password = "a test password 42"

    def __init__(self, set_server_conf=True):
        self.loc = os.path.dirname(os.path.abspath(__file__))
        self.testroot = tempfile.TemporaryDirectory(prefix="gintest")
        self.cmdloc = self.testroot.name
        os.chdir(self.cmdloc)
        self.env = os.environ.copy()
        # write configuration file for annex excludes and set up test server
        # config
        confdir = os.path.join(self.cmdloc, "conf")

        self.logdir = os.path.realpath(os.path.join(self.loc,  "..", "log"))
        os.makedirs(confdir, exist_ok=True)
        os.makedirs(self.logdir, exist_ok=True)

        self.outlog = os.path.join(self.logdir, "runner.log")

        self.log("== Initialised runner ==")
        self.log(f"Test directory: {self.cmdloc}")

        testbinloc = os.path.realpath(os.path.join(self.loc, "..", "bin"))
        self.env["PATH"] = testbinloc + os.pathsep + self.env["PATH"]
        self.env["GIN_CONFIG_DIR"] = confdir
        self.env["GIN_LOG_DIR"] = os.path.abspath(self.logdir)

        with open(os.path.join(confdir, "config.yml"), "w") as conffile:
            conffile.write(TESTCONFIG)
        self.repositories = dict()
        if set_server_conf:
            self._set_server_conf()


    def log(self, msg):
        with open(self.outlog, "a") as logfile:
            logfile.write(msg + "\n")

    def _set_server_conf(self):
        self.runcommand("gin", "add-server", "test",
                        "--web", "http://127.0.0.2:3000",
                        "--git", "git@127.0.0.2:2222",
                        inp="yes")
        self.runcommand("gin", "use-server", "test")

    def runcommand(self, *args, inp=None, exit=True):
        self.log(f"> {' '.join(args)}")
        if inp:
            self.log(f"Input: {inp}")
            inp += "\n"
        p = sp.run(args, env=self.env, stdout=sp.PIPE, stderr=sp.PIPE,
                   cwd=self.cmdloc, input=inp, encoding="utf-8")
        stdout, stderr = p.stdout.strip(), p.stderr.strip()
        # if exiting, force enable echo
        if stdout:
            self.log(f"Out: {stdout}")
        if stderr:
            self.log(f"Err: {stderr}")
        if p.returncode and exit:
            sys.exit(p.returncode)

        return stdout, stderr

    def cdrel(self, path="."):
        """
        Changes the working directory for the runner as well as the caller.

        With default argument '.', sets the working directory of the caller to
        the existing wd of the runner.
        """
        self.cmdloc = os.path.abspath(os.path.join(self.cmdloc, path))
        os.chdir(self.cmdloc)
        print(f"New dir: {self.cmdloc}")

    def login(self, username=username, password=password):
        self.username = username
        self.password = password
        return self.runcommand("gin", "login", username, inp=password)

    def cleanup(self):
        loc = self.cmdloc
        for location, repo in self.repositories.items():
            if repo:
                repopath = f"{self.username}/{repo}"
                self.runcommand("gin", "delete", repopath, inp=repopath)
        util.set_rwx_recursive(self.testroot.name)
        self.cmdloc = loc
        # cd out of tempdir
        self.cdrel("/")

    def logout(self):
        self.runcommand("gin", "logout", exit=False)
