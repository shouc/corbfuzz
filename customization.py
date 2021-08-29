import requests
import config
import utils
import hashlib
import os
import time
# import chromium_corb

s = requests.Session()

# s.post(f"http://{config.TARGET}/wp-login.php",
#        headers={'Cookie': 'wordpress_test_cookie=WP Cookie check'}, data={
#         "log": "shou",
#         "pwd": "shou@123",
#         "wp-submit": "Log In",
#         "redirect_to": config.TARGET,
#         "testcookie": "1"})

REQUEST_SESSION = s
CUSTOM_MUTATION = []

# put your oracle here:
def handler(result):
    # chromium_corb.save(result)
    return 1


RESP_HANDLER = handler
