import os
import util
from runner import Runner
import pytest


def revhash(r, num, paths=None):
    """
    Hash of n-th revision (1-based) for given paths (if paths is set) or entire
    repo. Reverse order, so 1 is HEAD
    """
    cmdargs = ["git", "rev-list", "-n", str(num), "HEAD"]
    if paths:
        cmdargs.extend(paths)
    revlist, _ = r.runcommand(*cmdargs, echo=False)
    revlist = revlist.splitlines()
    return revlist[-1]


def create_files(r):
    fnames = list()
    # make a few annex and git files
    os.makedirs("smallfiles", exist_ok=True)
    os.makedirs("datafiles", exist_ok=True)
    for idx in range(5):
        name = os.path.join("smallfiles", f"smallfile-{idx:03}")
        util.mkrandfile(name, 20)
        fnames.append(name)
    for idx in range(10):
        name = os.path.join("datafiles", f"datafile-{idx:03}")
        util.mkrandfile(name, 2000)
        fnames.append(name)
    return fnames


@pytest.mark.slow
def test_repo_versioning(runner):
    r = runner
    assert util.getrevcount(r) == r.commitcount

    head = revhash(r, 1)
    repofiles = list(r.hashes[head].keys())

    def checkout_and_compare(selection=None, revision=None,
                             fnames=None, dirnames=None):
        paths = list()
        if fnames:
            paths.extend(fnames)
        if dirnames:
            paths.extend(dirnames)

        # the hash of the pre-checkout revision (current HEAD)
        precorevhash = revhash(r, 1)

        if revision is None:
            # the hash of the commit we're going to checkout from
            oldrevhash = revhash(r, selection, paths)
        else:
            oldrevhash, _ = r.runcommand("git", "rev-parse", revision)

        # check if checkout should change any files
        cmdargs = ["git", "diff", oldrevhash]
        if paths:
            cmdargs.append("--")
            cmdargs.extend(paths)

        out, err = r.runcommand(*cmdargs, echo=False)
        expecting_changes = bool(out)
        if expecting_changes:
            r.commitcount += 1

        curtotalrev = util.getrevcount(r)

        if revision is None:
            cmdargs = ["gin", "version", "--max-count", "0"]
            inp = str(selection)
        else:
            cmdargs = ["gin", "version", "--id", revision]
            inp = None

        if paths:
            cmdargs.extend(paths)

        print(f"Running gin version command: {cmdargs} with input {inp}")
        r.runcommand(*cmdargs, inp=inp, echo=False)
        # should have a new commit now
        newn = util.getrevcount(r)
        assert expecting_changes == (newn == curtotalrev + 1),\
            "Version command did not create a new commit"
        # compute current hashes and compare with old entry in dict
        head, curhashes = util.hashtree(r)
        assert expecting_changes == (head not in r.hashes),\
            "New head same as an old head"
        r.hashes[head] = curhashes

        if fnames is not None or dirnames is not None:
            changedfiles = list()
            for fname in repofiles:
                if fnames and fname in fnames:
                    changedfiles.append(fname)
                elif dirnames:
                    for dirname in dirnames:
                        if fname.startswith(dirname):
                            changedfiles.append(fname)

            unchangedfiles = repofiles[:]
            for cf in changedfiles:
                unchangedfiles.remove(cf)
        else:
            # no args - all files changed (probably)
            changedfiles = repofiles[:]
            unchangedfiles = list()

        # compare all changed files with oldrevhash
        # and the rest with precorevhash
        for fname in changedfiles:
            if fname in r.hashes[oldrevhash]:
                assert curhashes[fname] == r.hashes[oldrevhash][fname]
                # else file didn't exist in oldrev
        for fname in unchangedfiles:
            assert curhashes[fname] == r.hashes[precorevhash][fname]

    checkout_and_compare(4)
    checkout_and_compare(8)
    checkout_and_compare(2)
    checkout_and_compare(10)
    checkout_and_compare(1)  # should do nothing

    # checkout_and_compare specific files
    checkout_and_compare(2, fnames=repofiles[3:])
    checkout_and_compare(5, fnames=repofiles[-1:])
    checkout_and_compare(8, fnames=repofiles[2:3])
    smallfiles = [fname for fname in repofiles
                  if fname.startswith("smallfiles")]
    datafiles = [fname for fname in repofiles if
                 fname.startswith("datafiles")]
    # name all small files
    checkout_and_compare(7, fnames=smallfiles)
    # name all data files
    checkout_and_compare(3, fnames=datafiles)
    # name all files
    checkout_and_compare(10, fnames=repofiles)
    # name directories
    checkout_and_compare(3, dirnames=["datafiles"])
    checkout_and_compare(3, dirnames=["smallfiles"])
    checkout_and_compare(6, fnames=datafiles, dirnames=["smallfiles"])
    checkout_and_compare(6, fnames=[datafiles[0], datafiles[5],
                                    datafiles[2]], dirnames=["smallfiles"])

    assert util.getrevcount(r) == r.commitcount

    revhashes = list(r.hashes.keys())

    checkout_and_compare(revision=revhashes[8])
    checkout_and_compare(revision=revhashes[4], fnames=repofiles[3:])
    checkout_and_compare(revision=revhashes[10], fnames=repofiles[-1:])
    checkout_and_compare(revision="HEAD~3", fnames=repofiles[2:3])
    checkout_and_compare(revision="master~10", dirnames=["smallfiles"])

    assert util.getrevcount(r) == r.commitcount


@pytest.mark.slow
def test_version_copyto(runner):
    r = runner

    # checkout some old file versions alongside current one
    def get_old_files(selection, paths, dest):
        curtotalrev = util.getrevcount(r)
        oldrevhash = revhash(r, selection, paths)
        cmdargs = ["gin", "version", "--max-count", "0",
                   "--copy-to", dest, *paths]
        print(f"Running gin version command: {cmdargs} with input {selection}")
        r.runcommand(*cmdargs, inp=str(selection), echo=True)
        # no new commits
        newn = util.getrevcount(r)
        assert newn == curtotalrev,\
            "New commit was created when it shouldn't"

        # get content for the checked out files
        r.runcommand("gin", "get-content", dest)
        # hash checked out file(s)
        # assumes all files in dest are from oldrevhash
        for fn in util.lsfiles(dest):
            cohash = util.md5sum(fn)
            origname = fn[len(dest)+1:-16]
            print(f"{fn} becomes {origname}")
            assert cohash == r.hashes[oldrevhash][origname],\
                "Checked out file hash verification failed"

    get_old_files(2, ["datafiles/datafile-003"], "oldstuff")
    get_old_files(7, ["datafiles/datafile-001"], "anotherolddir")
    get_old_files(3, ["smallfiles/smallfile-002"], "checkouts")
    get_old_files(5, ["smallfiles", "datafiles"], "everything")
    get_old_files(4, ["datafiles"], "olddatafiles")


@pytest.fixture(scope="module")
def runner():
    r = Runner()
    r.login()
    # create repo (remote and local) and cd into directory
    reponame = util.randrepo()
    print("Setting up test repository")
    r.runcommand("gin", "create", reponame,
                 "Test repository for versioning",
                 echo=False)
    r.cdrel(reponame)
    r.repositories[r.cmdloc] = reponame

    r.hashes = dict()
    head, curhashes = util.hashtree(r)
    r.hashes[head] = curhashes

    # add files and compute their md5 hashes
    create_files(r)
    out, err = r.runcommand("gin", "upload", ".", echo=False)
    head, curhashes = util.hashtree(r)
    r.hashes[head] = curhashes
    r.commitcount = 2

    # update all files 10 times
    print("Creating files")
    for _ in range(10):
        create_files(r)
        out, err = r.runcommand("gin", "upload", ".", echo=False)
        head, curhashes = util.hashtree(r)
        r.hashes[head] = curhashes
        r.commitcount += 1

    # verify commit count before returning
    assert util.getrevcount(r) == r.commitcount

    yield r

    r.cleanup()
    r.logout()

    print("DONE!")
