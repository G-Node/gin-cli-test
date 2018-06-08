from runner import Runner
import util
import pytest
import json


srva = ("gin", "add-server",
        "--web", "http://gintestserver:3000",
        "--git", "git@gintestserver:22",
        "srva")

srvb = ("gin", "add-server",
        "--web", "http://gintestserverb:3000",
        "--git", "git@gintestserverb:22",
        "srvb")


@pytest.fixture
def runner():
    r = Runner()

    yield r

    # cleanup
    r.cleanup()


def test_use_server_create_repo(runner):
    r = runner

    r.runcommand(*srva, inp="yes")
    r.runcommand(*srvb, inp="yes")

    repo_srva = util.randrepo()
    repo_srvb = util.randrepo()

    def cleanup():
        r.runcommand("gin", "use-server", "srva")
        repopath = f"{r.username}/{repo_srva}"
        r.runcommand("gin", "delete", repopath, inp=repopath)

        r.runcommand("gin", "use-server", "srvb")
        repopath = f"{r.username}/{repo_srvb}"
        r.runcommand("gin", "delete", repopath, inp=repopath)

        r.runcommand("gin", "use-server", "srva")
        r.runcommand("gin", "logout")
        r.runcommand("gin", "use-server", "srvb")
        r.runcommand("gin", "logout")

        r.runcommand("gin", "remove-server", "srva")
        r.runcommand("gin", "rm-server", "srvb")

    r.cleanup = cleanup

    r.runcommand("gin", "use-server", "srvb")
    r.login()

    r.runcommand("gin", "create", repo_srvb,
                 "Test multiple servers (switching default)")

    out, err = r.runcommand("gin", "repos", "--json", echo=False)
    repos = json.loads(out)
    # find repo_srva
    for repo in repos:
        if repo["name"] == repo_srvb:
            break
    else:
        assert False, "Unable to find repository on server"

    # change server, check repos
    r.runcommand("gin", "use-server", "srva")
    r.login()

    out, err = r.runcommand("gin", "repos", "--json", echo=False)
    if out:
        repos = json.loads(out)
        for repo in repos:
            assert repo["name"] != repo_srvb

    r.runcommand("gin", "create", repo_srva,
                 "Test multiple servers (switching default)")

    r.runcommand("gin", "use-server", "srvb")

    # TODO: Change when we get --json output for the server listing
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 3, f"{servercount} servers configured; expected 3"

    r.runcommand("gin", "rm-server", "srva")
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 2, f"{servercount} servers configured; expected 2"

    r.runcommand("gin", "rm-server", "srvb")
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 1, f"{servercount} servers configured; expected 1"

    r.runcommand(*srva, inp="yes")
    r.runcommand(*srvb, inp="yes")


def test_flag_server_create_repo(runner):
    r = runner

    r.runcommand(*srva, inp="yes")
    r.runcommand(*srvb, inp="yes")

    repo_srva = util.randrepo()
    repo_srvb = util.randrepo()

    def cleanup():
        repopath = f"{r.username}/{repo_srva}"
        r.runcommand("gin", "delete", "--server=srva",
                     repopath, inp=repopath)
        r.runcommand("gin", "logout", "--server", "srva")

        repopath = f"{r.username}/{repo_srvb}"
        r.runcommand("gin", "delete", "--server", "srvb",
                     repopath, inp=repopath)
        r.runcommand("gin", "logout", "--server", "srvb")

        r.runcommand("gin", "remove-server", "srva")
        r.runcommand("gin", "rm-server", "srvb")

    r.cleanup = cleanup

    r.runcommand("gin", "login", "--server", "srvb",
                 r.username, inp=r.password)

    r.runcommand("gin", "create", "--server", "srvb", repo_srvb,
                 "Test multiple servers (server flag)")

    out, err = r.runcommand("gin", "repos", "--server", "srvb",
                            "--json", echo=False)
    repos = json.loads(out)
    # find repo_srva
    for repo in repos:
        if repo["name"] == repo_srvb:
            break
    else:
        assert False, "Unable to find repository on server"

    r.runcommand("gin", "login", "--server", "srva",
                 r.username, inp=r.password)

    out, err = r.runcommand("gin", "repos", "--server", "srva",
                            "--json", echo=False)
    if out:
        repos = json.loads(out)
        for repo in repos:
            assert repo["name"] != repo_srvb

    r.runcommand("gin", "create", "--server", "srva", repo_srva,
                 "Test multiple servers (server flag)")

    # TODO: Change when we get --json output for the server listing
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 3, f"{servercount} servers configured; expected 3"

    r.runcommand("gin", "rm-server", "srva")
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 2, f"{servercount} servers configured; expected 2"

    r.runcommand("gin", "rm-server", "srvb")
    out, err = r.runcommand("gin", "servers")
    assert not err, "error getting 'gin servers' listing"
    servercount = len([line for line in out.splitlines()
                       if line.startswith("*")])
    assert servercount == 1, f"{servercount} servers configured; expected 1"

    r.runcommand(*srva, inp="yes")
    r.runcommand(*srvb, inp="yes")
