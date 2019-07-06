import os
import sys
from datetime import datetime
import requests
import json


def read_files(path):
    now = datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
    files = os.listdir(path)
    filedata = dict()
    for fname in files:
        with open(os.path.join(path, fname)) as f:
            filedata[fname] = {
                "content": f.read()
            }
    data = {
        "description": f"Test ended {nowstr}",
        "files": filedata
    }
    return data


def main():
    logpath = sys.argv[1]
    token = os.environ["GISTTOKEN"]
    data = read_files(logpath)

    gistid = "23d5ff4cc52a4ac406c4acbd74220a9c"
    url = f"https://api.github.com/gists/{gistid}"
    header = {
        "content-type": "application/jsonAuthorization",
        "Authorization": f"token {token}"
    }

    r = requests.post(url, data=json.dumps(data), headers=header)
    if r.status_code == requests.codes.ok:
        print(f"Logs uploaded to {url}")
    else:
        print(f"Log upload failed")


if __name__ == "__main__":
    main()
