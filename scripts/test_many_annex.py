"""
Test issue with adding many large (100s MB) annex files.
"""
import os
from runner import Runner
import util
import pytest


@pytest.fixture
def runner():
    r = Runner()
    r.login()

    reponame = util.randrepo()
    r.runcommand("gin", "create", reponame,
                 "Test repository for multi add annex")
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame
    r.reponame = reponame

    yield r

    r.cleanup()
    r.logout()


def test_annex_filters(runner):
    r = runner

    N = 4
    # Create some big data files
    for idx in range(N):
        util.mkrandfile(f"randfile{idx}", 200000)  # 10x 200 MB files

    r.runcommand("gin", "upload", ".")

    # files should be links
    for idx in range(N):
        assert os.path.islink(f"randfile{idx}")

    status = util.zerostatus()
    status["OK"] = N
    util.assert_status(r, status=status)

    r.runcommand("gin", "remove-content", ".")

    status["OK"] = 0
    status["NC"] = N
    util.assert_status(r, status=status)
