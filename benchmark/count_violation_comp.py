import os, sys

dir = "/tmp/cbc"
REPO_DIR = sys.argv[1]


def comp_should_eq(a, b):
    a = int(a)
    b = int(b)
    if a > 6 or b > 6:
        return True
    if a in [4,5] and b in [4,5]:
        return True
    if a in [2,3] and b in [2,3]:
        return True
    return a == b

ft = [x[:-1] for x in open("funct.txt").readlines()]
ft = {x.split(" @ ")[0]: eval(x.split(" @ ")[1]) for x in ft}


def internal_func(funct_name, args):
    if funct_name in ft:
        func_arg = ft[funct_name]
        if len(args) > len(func_arg):
            return False
        for k, i in enumerate(args):
            if i not in func_arg[k] and 9 not in func_arg[k]:
                return False
    return True

for folder in os.listdir(REPO_DIR):
    cter1= 0
    gcter1 = 0
    if folder.endswith(".txt"):
        continue
    try:
        cbcs = eval(open(f"{REPO_DIR}/{folder}/cbc.txt").readline())
        for i in cbcs:
            cdir = dir + "/" + i
            with open(cdir) as fp:
                lines = fp.readlines()
                for j in lines:
                    args = [x for x in j.split(":")[-1]][:-1]
                    func = ":".join(j.split(":")[:-1])
                    if func == "comp":
                        if comp_should_eq(args[0], args[1]):
                            cter1 += 1
                        gcter1 += 1
    except:
        pass

    # cter = 0
    # gcter = 0
    # cbcs = eval(open(f"/home/shou/repos_ok2/{folder}/cbc2.txt").readline())
    # for i in cbcs:
    #     cdir = dir + "/" + i
    #     with open(cdir) as fp:
    #         lines = fp.readlines()
    #         for j in lines:
    #             args = [x for x in j.split(":")[-1]][:-1]
    #             func = ":".join(j.split(":")[:-1])
    #             if func != "comp":
    #                 if internal_func(func, args):
    #                     # print(1)
    #                     cter += 1
    #                 gcter += 1
    # try:
    #     cbcs = eval(open(f"/home/shou/repos_ok/{folder}/cbc3.txt").readline())
    #     for i in cbcs:
    #         cdir = dir + "/" + i
    #         with open(cdir) as fp:
    #             lines = fp.readlines()
    #             for j in lines:
    #                 args = [x for x in j.split(":")[-1]][:-1]
    #                 func = ":".join(j.split(":")[:-1])
    #                 if func != "comp":
    #                     if internal_func(func, args):
    #                         # print(1)
    #                         cter += 1
    #                     gcter += 1
    # except:
    #     pass

    print(folder, cter1, gcter1)
