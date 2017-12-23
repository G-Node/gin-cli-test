import sys
import os
import subprocess as sp
import tempfile


class Runner(object):

    username = "testuser"

    def __init__(self):
        self.loc = os.path.dirname(os.path.abspath(__file__))
        self.env = {
            "PATH": os.environ.get("PATH"),
            "GIN_CONFIG": os.path.join(self.loc,
                                       "conf/g-node/gin/config.yml"),
            "GIN_LOG": os.path.join(self.loc, "log/gin/gin.log"),
        }
        self.testroot = tempfile.TemporaryDirectory(prefix="gintest")
        self.cmdloc = self.testroot.name
        os.chdir(self.cmdloc)

    def runcommand(self, *args, inp=None, exit=True):
        print(f"> {' '.join(args)}")
        if inp:
            inp += "\n"
        p = sp.run(args, env=self.env, stdout=sp.PIPE, stderr=sp.PIPE,
                   cwd=self.cmdloc, input=inp, encoding="utf-8")
        stdout, stderr = p.stdout.strip(), p.stderr.strip()
        if stdout:
            print(f"{stdout}")
        if stderr:
            print(f"E: {stderr}")
        if p.returncode and exit:
            sys.exit(p.returncode)
        return stdout, stderr

    def cdrel(self, path):
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
