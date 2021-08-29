import re
try:
    import docker
except ImportError:
    pass

USE_DOCKER = False
# Don't Use Docker
TARGET = "localhost:1194/"
HOST_NAMES_CARED = [TARGET]

# Use Docker
DOCKER_INSTANCE = docker.from_env() if USE_DOCKER else None
DOCKER_FILE_LOC = ""

# Config for Crawling
REDIS_HOST = "localhost"
REDIS_PORT = 6379
WAIT_TIME = 1
IGNORE_LINKS = [re.compile("logout")]
DONT_CARE_STATUS_CODE = [404, 502, 500, 403]

