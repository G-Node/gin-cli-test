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
    for filepath in gitfiles:
        msum = md5sum(filepath)
        curtree[filepath] = msum
        print(f"{filepath}: {msum}")

    return head, curtree


def commitnum(r):
    ncommits, _ = r.runcommand("git", "rev-list", "--count", "HEAD",
                               echo=False)
    return int(ncommits)


def revhash(r, num):
    revlist, _ = r.runcommand("git", "rev-list", "--reverse", "HEAD",
                              echo=False)
    revlist = revlist.splitlines()
    return revlist[num]


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
    r.runcommand("gin", "create", reponame,
                 "Test repository for versioning. Created with test scripts")
    r.cdrel(reponame)

    head, curhashes = hashtree(r)
    hashes[head] = curhashes

    # add files and manually compute their md5 hashes
    repofiles = create_files(r)
    out, err = r.runcommand("gin", "upload", ".")
    head, curhashes = hashtree(r)
    hashes[head] = curhashes

    # update all files 10 times
    for _ in range(10):
        r.runcommand("gin", "unlock", ".")
        create_files(r)
        out, err = r.runcommand("gin", "upload", ".")
        head, curhashes = hashtree(r)
        hashes[head] = curhashes

    def checkout_and_compare(targetrevnum, fnames=None, dirnames=None):
        curn = commitnum(r)
        selection = str(curn-targetrevnum)

        cmdargs = ["gin", "version", "--max-count", "0"]
        if fnames:
            cmdargs.extend(fnames)

        if dirnames:
            cmdargs.extend(dirnames)

        r.runcommand(*cmdargs, inp=selection)
        # compute current hashes and compare with old entry in dict
        # this assumes ordered dictionaries
        head, curhashes = hashtree(r)
        hashes[head] = curhashes

        # the hash of the old revision (the one we checked out from)
        oldrevhash = revhash(r, targetrevnum)
        # the hash of the previous revision, before the checkout
        prevrevhash = revhash(r, -1)

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
        # compare all changed files with oldrevhash
        # and the rest with prevrevhash
        for fname in changedfiles:
            if fname in hashes[oldrevhash]:
                assert curhashes[fname] == hashes[oldrevhash][fname]
                # else file didn't exist in oldrev
        for fname in unchangedfiles:
            assert curhashes[fname] == hashes[prevrevhash][fname]

    checkout_and_compare(4)
    checkout_and_compare(8)
    checkout_and_compare(2)
    checkout_and_compare(0)

    # checkout_and_compare specific files
    checkout_and_compare(2, fnames=repofiles[3:])
    checkout_and_compare(2, fnames=repofiles[2:3])
    checkout_and_compare(5, fnames=repofiles[-1:])
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

    r.runcommand("git", "log")

    r.cleanup(reponame)
    r.logout()

    print("DONE!")
