import os
import util
from random import randint
from runner import Runner
from hashlib import md5


def md5sum(filename, printhash=False):
    with open(filename, "rb") as thefile:
        fdata = thefile.read()
        msum = md5(fdata).hexdigest()
    return msum


def hashtree(r):
    curtree = dict()
    head, err = r.runcommand("git", "rev-parse", "HEAD", echo=False)
    print(f"Hashing files in working tree (at {head})")

    gitfiles, err = r.runcommand("git", "ls-files", echo=False)
    gitfiles = gitfiles.splitlines()
    r.runcommand("gin", "get-content", ".", echo=False)
    r.runcommand("gin", "unlock", ".", echo=False)
    for filepath in gitfiles:
        msum = md5sum(filepath)
        curtree[filepath] = msum
        # print(f"{filepath}: {msum}")

    r.runcommand("gin", "lock", ".", echo=False)
    return head, curtree


def getrevcount(r):
    """
    Total number of revisions from HEAD.
    """
    n, _ = r.runcommand("git", "rev-list", "--count", "HEAD",
                               echo=False)
    return int(n)


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


def test_versioning():
    hashes = dict()
    r = Runner()

    r.login()
    # username = r.username

    # create repo (remote and local) and cd into directory
    reponame = f"gin-test-{randint(0, 9999):04}"
    # repopath = f"{username}/{reponame}"
    print("Setting up test repository")
    r.runcommand("gin", "create", reponame,
                 "Test repository for versioning. Created with test scripts",
                 echo=False)
    r.cdrel(reponame)

    head, curhashes = hashtree(r)
    hashes[head] = curhashes

    # add files and manually compute their md5 hashes
    repofiles = create_files(r)
    out, err = r.runcommand("gin", "upload", ".", echo=False)
    head, curhashes = hashtree(r)
    hashes[head] = curhashes

    # update all files 10 times
    print("Creating files")
    for _ in range(10):
        r.runcommand("gin", "unlock", ".", echo=False)
        create_files(r)
        out, err = r.runcommand("gin", "upload", ".", echo=False)
        head, curhashes = hashtree(r)
        hashes[head] = curhashes

    assert getrevcount(r) == 12

    def checkout_and_compare(selection, fnames=None, dirnames=None):
        paths = list()
        if fnames:
            paths.extend(fnames)
        if dirnames:
            paths.extend(dirnames)

        # the hash of the pre-checkout revision (current HEAD)
        precorevhash = revhash(r, 1)
        # the hash of the commit we're going to checkout from
        oldrevhash = revhash(r, selection, paths)

        # check if checkout should change any files
        cmdargs = ["git", "diff", oldrevhash]
        if paths:
            cmdargs.append("--")
            cmdargs.extend(paths)

        out, err = r.runcommand(*cmdargs, echo=False)
        expecting_changes = bool(out)

        curtotalrev = getrevcount(r)

        cmdargs = ["gin", "version", "--max-count", "0"]
        if paths:
            cmdargs.extend(paths)

        print(f"Running gin version command: {cmdargs} with input {selection}")
        r.runcommand(*cmdargs, inp=str(selection), echo=False)
        # should have a new commit now
        newn = getrevcount(r)
        assert expecting_changes == (newn == curtotalrev + 1),\
            "Version command did not create a new commit"
        # compute current hashes and compare with old entry in dict
        head, curhashes = hashtree(r)
        assert expecting_changes == (head not in hashes),\
            "New head same as an old head"
        hashes[head] = curhashes

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
            if fname in hashes[oldrevhash]:
                assert curhashes[fname] == hashes[oldrevhash][fname]
                # else file didn't exist in oldrev
        for fname in unchangedfiles:
            assert curhashes[fname] == hashes[precorevhash][fname]

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
    checkout_and_compare(6, fnames=[datafiles[0], datafiles[5], datafiles[2]],
                         dirnames=["smallfiles"])

    assert getrevcount(r) == 24

    r.cleanup(reponame)
    r.logout()

    print("DONE!")


if __name__ == "__main__":
    test_versioning()
