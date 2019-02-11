import sys
import os
from pathlib import Path
import shutil
import subprocess as sp
import tempfile


class Runner(object):

    username = "testuser"
    password = "a test password 42"

    def __init__(self):
        self.loc = os.path.dirname(os.path.abspath(__file__))
        self.testroot = tempfile.TemporaryDirectory(prefix="gintest")
        self.cmdloc = self.testroot.name
        os.chdir(self.cmdloc)
        self.env = os.environ
        # copy configuration to temporary directory
        userhome = Path.home().absolute()
        origconf = os.path.join(userhome, "conf", "config.yml")
        confdir = os.path.join(self.cmdloc, "conf")
        os.mkdir(confdir)
        self.env["GIN_CONFIG_DIR"] = confdir
        shutil.copy(origconf, confdir)
        self.env["GIN_LOG_DIR"] = os.path.join(userhome, "log")
        self.repositories = dict()

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

    def login(self, username=username, password=password):
        self.username = username
        self.password = password
        return self.runcommand("gin", "login", username, inp=password)

    def cleanup(self):
        def runsilent(*args):
            self.runcommand(*args, exit=False, echo=False)
        loc = self.cmdloc
        for location, repo in self.repositories.items():
            print(f"Cleaning up {location} ({repo})")
            self.cmdloc = location
            runsilent("gin", "annex", "sync")
            runsilent("gin", "annex", "unused")
            runsilent("gin", "annex", "dropunused")
            runsilent("gin", "annex", "uninit")
            # bare repos don't uninit properly and keep data behind
            # changing permissions for cleanup
            for root, dirs, files in os.walk(location):
                for d in dirs:
                    dname = os.path.join(root, d)
                    os.chmod(dname, 0o770)
                for f in files:
                    fname = os.path.join(root, f)
                    if os.path.exists(fname):  # skip broken links
                        os.chmod(fname, 0o770)
            if repo:
                repopath = f"{self.username}/{repo}"
                self.runcommand("gin", "delete", repopath, inp=repopath)
        self.cmdloc = loc

    def logout(self):
        self.runcommand("gin", "logout", exit=False, echo=False)
