# THIS CODE IS DEPRECATED & SAFE TO REMOVE
import os
import sys

REPO_DIR = sys.argv[1]

def evaluate_cov(folder, cov):
    bitmap_glob = {}
    cov_count = 0
    for covf in os.listdir(f"{REPO_DIR}/{folder}/{cov}/"):
        bitmap = eval(open(f"{REPO_DIR}/{folder}/{cov}/{covf}").readline())
        new_cov = False
        for i in bitmap:
            cnt = bitmap[i]
            available_bucket = 0b1111
            if i in bitmap_glob:
                available_bucket = int(bitmap_glob[i])
            has_new_cov = False
            new_bucket = available_bucket
            if cnt == 1 and available_bucket & 1:
                has_new_cov = True
                new_bucket &= 0b1110
            elif cnt == 2 and available_bucket & 2:
                has_new_cov = True
                new_bucket &= 0b1101
            elif cnt < 8 and available_bucket & 4:
                has_new_cov = True
                new_bucket &= 0b1011
            elif available_bucket & 8:
                has_new_cov = True
                new_bucket &= 0b0111
            if has_new_cov:
                bitmap_glob[i] = new_bucket
                new_cov = True
        if new_cov:
            cov_count += 1
    return cov_count


for folder in os.listdir(REPO_DIR):
    print(evaluate_cov(folder, "cov"))#, evaluate_cov(folder, "cov_all"))
