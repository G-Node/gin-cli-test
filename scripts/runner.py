import sys
import os
import subprocess as sp
import tempfile


class Runner(object):

    username = "testuser"

    def __init__(self):
        self.loc = os.path.dirname(os.path.abspath(__file__))
        self.env = os.environ
        self.env["GIN_CONFIG_DIR"] = os.path.join(self.loc, "conf")
        self.env["GIN_LOG_DIR"] = os.path.join(self.loc, "log")
        self.testroot = tempfile.TemporaryDirectory(prefix="gintest")
        self.cmdloc = self.testroot.name
        os.chdir(self.cmdloc)

    def runcommand(self, *args, inp=None, exit=True, echo=True):
        def doecho(msg):
            if echo:
                print(msg)
        doecho(f"> {' '.join(args)}")
        if inp:
            doecho(f"Input: {inp}")
            inp += "\n"
        p = sp.run(args, env=self.env, stdout=sp.PIPE, stderr=sp.PIPE,
                   cwd=self.cmdloc, input=inp, encoding="utf-8")
        stdout, stderr = p.stdout.strip(), p.stderr.strip()
        # if exiting, force enable echo
        if p.returncode and exit:
            echo = True
        if stdout:
            doecho(f"{stdout}")
        if stderr:
            doecho(f"{stderr}")
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

    def login(self, username=username, password="a test password 42"):
        self.username = username
        return self.runcommand("gin", "login", username, inp=password)

    def cleanup(self, repo):
        repopath = f"{self.username}/{repo}"
        self.runcommand("gin", "annex", "uninit", exit=False)
        self.runcommand("gin", "delete", repopath, inp=repopath)

    def logout(self):
        self.runcommand("gin", "logout")
