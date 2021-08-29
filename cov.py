import requests
import utils
import uuid
import docker_utils


# Bucket 1: 1
# Bucket 2: 2
# Bucket 3: 8
# Bucket 4: 128

def get_cov_header():
    return str(uuid.uuid4())


def get_cov(cov_uuid):
    url = f'http://{docker_utils.get_target()}/cov/{cov_uuid}.txt'
    result = requests.get(url).content
    try:
        result = eval(result)
        assert type(result) == dict
        return result
    except Exception as e:
        utils.ERROR(f"Error at deserializing cov map {e}")
        return {}


COV_COUNT = 0


def get_global_cov():
    cov = utils.REDIS_OBJ.hgetall("coverage")
    return cov


def evaluate_cov(cov_uuid):
    bitmap = get_cov(cov_uuid)
    bitmap_glob = get_global_cov()
    new_cov = False
    global COV_COUNT
    for i in bitmap:
        cnt = bitmap[i]
        i_b = str(i).encode('latin-1')
        available_bucket = 0b1111
        if i_b in bitmap_glob:
            available_bucket = int(bitmap_glob[i_b])
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
            COV_COUNT += 1
            utils.REDIS_OBJ.hset("coverage", i, new_bucket)
            new_cov = True
    if new_cov:
        utils.INFO(f"New cov found! Count: {COV_COUNT}")
    else:
        utils.DEBUG(f"Not new cov")
    return new_cov
