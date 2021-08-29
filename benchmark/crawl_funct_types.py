# THIS CODE IS DEPRECATED & SAFE TO REMOVE

import requests
from bs4 import BeautifulSoup as bs4
import os, threading, random, sys

def get_funct_table():
    content = bs4(requests.get("https://www.php.net/manual/en/indexes.functions.php").content, features="lxml")
    funct_table = []
    for i in (content.find(attrs={
        "class": "gen-index index-for-refentry"
    }).find_all("a")):
        funct_table.append((i.get_text(), i.get("href")))

    return funct_table


# def get_description(url):
#     try:
#         content = bs4(requests.get(f"https://www.php.net/manual/en/{url[1]}").content, features="lxml")
#         method = content.findAll(attrs={
#             "class": "methodparam"
#         })
#
#         print(url[0], [x.find(attrs={"class": "type"}).get_text() for x in method])
#     except:
#         print(url[0], "error")
#
# table = get_funct_table()
# print(table)
#
# # for i in table:
# #     try:
# #         href = table[i]
# #         print(i, get_description(href))
# #     except:
# #         print(i)
#
# urls = get_funct_table()
#
# n = 40  # number of parallel connections
# chunks = [urls[i * n:(i + 1) * n] for i in range((len(urls) + n - 1) // n)]
#
# lock = threading.Lock()
#
# for chunk in chunks:
#     threads = []
#     for url in chunk:
#         thread = threading.Thread(target=get_description, args=(url,))
#         thread.start()
#         threads.append(thread)
#     for thread in threads:
#         thread.join()

#
# with open("funct.txt") as fp:
#     for i in fp.readlines():
#         ats = "".join(i.split(" ")[1:])
#         print(eval(ats))
# for i in os.listdir("doc-en/reference/"):
#     for j in os.listdir(f"doc-en/reference/{i}/functions"):
#         with open(f"doc-en/reference/{i}/functions/{j}") as fp:
#             bs = bs4(fp.read(), features="lxml")
#             param = bs.find("methodparam")
#             name = bs.find("methodname")
#             print(name, param)

arr = {
    "float": [5],
    "int": [4],
    "string": [6],
    "bool": [2, 3],
    "null": [1]
}

for i in open("doc-en/reff.txt").readlines():
    with open("doc-en/" + i.replace("\n", "")) as fp:
        try:
            bs = bs4(fp.read(), features="lxml")
        except:
            continue
        param = bs.findAll("methodparam")
        name = bs.find("methodname")
        if not name:
            continue
        pp = []
        if param:
            try:
                for x in param:
                    p = []
                    for j in x.find_all("type"):
                        if j.get_text() in arr:
                            p += arr[j.get_text()]
                        else:
                            p += [9]
                pp.append(p)
            except:
                continue
        print(name.get_text(), "@", (pp))
