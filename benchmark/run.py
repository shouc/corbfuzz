import os, time, sys

REPO_DIR = sys.argv[1]

for _ in range(2):
    os.system("pkill -f -9 \"php\"")
    os.system("pkill -f -9 \"node\"")
    os.system("pkill -f -9 \"chrom\"")
    for i in os.listdir(REPO_DIR):
        folder = REPO_DIR + "/" + i
        os.system(f"rm -rf {folder}/cov && mkdir {folder}/cov")
        os.chdir(folder)
        for m in range(10):
            os.system(f"php "
                      f"-dextension=/corbfuzz/hsfuzz.so -S 0.0.0.0:{1194 + m} &")

        os.chdir(f"/corbfuzz/fake_mysql")
        os.system(f"./run.sh log/{i} &")
        time.sleep(1)

        init_cbc = os.listdir("/tmp/cbc")
        init_fd = os.listdir("/tmp/page")

        os.chdir(f"/corbfuzz")
        os.system("timeout 7m python3 start.py")

        os.system("pkill -f -9 \"php\"")
        os.system("pkill -f -9 \"node\"")
        os.system("pkill -f -9 \"chrom\"")

        end_cbc = set(os.listdir("/tmp/cbc"))
        end_fd = set(os.listdir("/tmp/page"))

        r = end_cbc.difference(init_cbc)
        k = end_fd.difference(init_fd)

        with open(f"{REPO_DIR}/{i}/cbc.txt", "a+") as fp:
            fp.write(str(r) + "\n")
        with open(f"{REPO_DIR}/{i}/fd.txt", "a+") as fp:
            fp.write(str(k) + "\n")
        time.sleep(3)
# /home/shou/repos/43337c58-1368-4e5a-809f-13de404cd475
