import time

import os
import uuid
import config
import utils


def create_image(docker_file_path: str):
    docker_file = open(docker_file_path + "/Dockerfile").read()
    build_id = uuid.uuid4()
    tmp_file_path = f"/tmp/{build_id}"
    os.system(f"cp -R {docker_file_path} {tmp_file_path}")
    with open(f"{tmp_file_path}/Dockerfile", "w") as fp:
        fp.write(docker_file)
    config.DOCKER_INSTANCE.images.build(path=tmp_file_path, tag=build_id)
    return build_id


def spin_up_container(build_id: str):
    assert build_id in config.DOCKER_INSTANCE.images.list()
    container_id = config.DOCKER_INSTANCE.containers.run(build_id, detach=True).id
    time.sleep(10)
    utils.INFO("Spinning up the container....")
    container = config.DOCKER_INSTANCE.containers.get(container_id)
    utils.REDIS_OBJ.set("target", container.attrs['NetworkSettings']['IPAddress'])
    return container


def get_target():
    if config.USE_DOCKER:
        while not utils.REDIS_OBJ.get("target"):
            time.sleep(config.WAIT_TIME)
        return utils.REDIS_OBJ.get("target").decode("latin-1")
    return config.TARGET
