import hashlib
import json, uuid,os
import sys

for i in (json.load(open("repos.txt"))):
    os.system(f"git clone https://github.com/{i} {sys.argv[1]}/{hashlib.md5(i.encode('utf-8')).hexdigest()}")

