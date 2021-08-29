import os
import sys
os.chdir(sys.argv[1])
for folder in os.listdir():
    if folder.endswith(".txt"):
        continue
    # with open(f"/home/shou/coding/hsfuzz/fake_mysql/log/{folder}") as fp:
    #     if len(fp.read()) > 28:
    #         os.system(f"mv /home/shou/repos/{folder} /home/shou/repos_ok2/")
    final_res1 = {}
    final_res2 = {}
    # for i in os.listdir(folder + "/cov_all"):
    #     path = folder + "/cov_all/" + i
    #     with open(path) as fp:
    #         content = fp.read()
    #         res = eval(content)
    #         for k in res:
    #             final_res1[k] = 1
    try:
        for i in os.listdir(folder + "/cov"):
            path = folder + "/cov/" + i
            with open(path) as fp:
                content = fp.read()
                res = eval(content)
                for k in res:
                    final_res2[k] = 1
    except:
        pass
    # if len(final_res1) == 0:
    print(folder, str(len(final_res2)))
    # if len(final_res2) < 1: # remove websites with no index.php
    #     os.system(f"rm -rf {folder}")
    # os.system(f"mv {folder}/cov_all/cov {folder}/cov_rand")