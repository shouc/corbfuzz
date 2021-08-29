import redis
from rq import Queue
from rpq.RpqQueue import RpqQueue

REDIS_OBJ = redis.Redis(host='localhost', port=6379, db=0)
JOB_QUEUE = Queue(connection=REDIS_OBJ)
PRIORITY_QUEUE = RpqQueue(REDIS_OBJ, 'urls')
REDIS_OBJ.flushall()


class Colors:
    HEADER = '\033[35m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def INFO(x, name="X"):
    print(f"{Colors.BOLD}{Colors.HEADER}[INFO: {name}]    {x}{Colors.ENDC}{Colors.ENDC}")


def DEBUG(x, name="X"):
    # print(f"{Colors.BOLD}{Colors.GREEN}[DEBUG: {name}]{Colors.ENDC}{Colors.ENDC}   {x}")
    pass


def ERROR(x, name="X"):
    print(f"{Colors.BOLD}{Colors.RED}[ERROR: {name}]{Colors.ENDC}{Colors.ENDC}   {x}")


def WARN(x, name="X"):
    print(f"{Colors.BOLD}{Colors.YELLOW}[WARNING: {name}]{Colors.ENDC}{Colors.ENDC} {x}")
