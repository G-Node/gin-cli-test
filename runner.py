import sys
import os
import subprocess as sp
import tempfile


class Runner(object):

    def __init__(self):
        self.loc = os.path.dirname(os.path.abspath(__file__))
        self.env = {
            "PATH": os.environ.get("PATH"),
            "XDG_CONFIG_HOME": os.path.join(self.loc, "conf"),
            "XDG_CACHE_HOME": os.path.join(self.loc, "log"),
        }
        self.testroot = tempfile.TemporaryDirectory(prefix="gintest")
        self.cmdloc = self.testroot.name

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
        print(f"New dir: {self.cmdloc}")
