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
    # make a few annex and git files
    r.cdrel("smallfiles")
    for idx in range(5):
        util.mkrandfile(f"smallfile-{idx:03}", 20)
    r.cdrel("..")
    r.cdrel("datafiles")
    for idx in range(10):
        util.mkrandfile(f"datafile-{idx:03}", 2000)
    r.cdrel("..")


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
    os.mkdir("smallfiles")
    os.mkdir("datafiles")

    head, curhashes = hashtree(r)
    hashes[head] = curhashes

    # add files and manually compute their md5 hashes
    create_files(r)
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

    def checkout_and_compare(targetrevnum):
        curn = commitnum(r)
        selection = str(curn-targetrevnum)

        r.runcommand("gin", "version", "0", inp=selection)
        # compute current hashes and compare with old entry in dict
        # this assumes ordered dictionaries
        head, curhashes = hashtree(r)
        hashes[head] = curhashes

        oldhash = revhash(r, targetrevnum)
        # comparing only files that exist in oldhash, since our checkout
        # doesn't remove files from git
        for fname, fhash in hashes[oldhash].items():
            assert fhash == curhashes[fname]

    checkout_and_compare(4)
    checkout_and_compare(8)
    checkout_and_compare(2)
    checkout_and_compare(0)

    r.runcommand("git", "log")

    r.cleanup(reponame)
    r.logout()

    print("DONE!")
