import time
import requests
import config
import customization
import mutator
import utils
import docker_utils
from urllib.parse import urlparse, ParseResult, urlunparse
from bs4 import BeautifulSoup
import re
import cov
import prior
from browsers import *


# convert a link to an url
# e.g. convert http://localhost:1194/test.php?id=1#111 to /test.php?id=1
def link_to_url(link: str) -> str:
    # discard domain, fragment, and
    url_obj = urlparse(link)
    if url_obj.scheme not in ["http", "https", ""]:
        # not the protocol we care
        return ''
    # if url_obj.hostname and url_obj.hostname not in config.HOST_NAMES_CARED:
    if url_obj.hostname and ("localhost" not in url_obj.hostname or "127.0.0.1" not in url_obj.hostname):
        return ''
    return urlunparse(ParseResult(
        scheme='',
        netloc='',
        path=url_obj.path,
        params=url_obj.params,
        query=url_obj.query,
        fragment=''))

# determine whether a link should be ignored
def should_ignore_link(link: str):
    for l in config.IGNORE_LINKS:
        if l.match(link):
            return True
    return False

# extract possible links in the HTML and for each link, crawl it if it is new
def extract_links(content: str, seed: int, selenium_obj) -> [str]:
    soup = BeautifulSoup(content, features="lxml")
    for link in soup.findAll('a', attrs={'href': re.compile(".+?")}):
        link = link_to_url(link["href"])
        if link == '':
            continue
        if not utils.REDIS_OBJ.hexists("already_crawled", f"{link}%%{seed}") and not should_ignore_link(link):
            crawl_with_eval(link, seed, selenium_obj)

# extract possible links in the requests (e.g., API calls, etc.) and for each link, crawl it if it is new
def extract_links2(seed: int, selenium_obj) -> [str]:
    for link in selenium_obj.requests:
        link = link_to_url(link.url)
        if link == '':
            continue
        if not utils.REDIS_OBJ.hexists("already_crawled", f"{link}%%{seed}") and not should_ignore_link(link):
            crawl_with_eval(link, seed, selenium_obj)

# get a link from the corpus
def get_link_from_redis():
    url = utils.REDIS_OBJ.srandmember("url_seed")
    if not url:
        return None
    return url

TARGET = None

# crawl a link
def crawl_link(link: str, seed: int, selenium_obj):
    utils.REDIS_OBJ.hset("already_crawled", f"{link}%%{seed}", "1")
    url = f'http://{TARGET}/{link}'
    utils.INFO(url)
    cov_uuid = cov.get_cov_header()

    def interceptor(request):
        request.headers['Cov-Loc'] = cov_uuid
        request.headers['Seed'] = str(seed)

    # result = customization.REQUEST_SESSION.get(url, headers={
    #     "Cov-Loc": cov_uuid,
    #     "Seed": str(seed)
    # })
    selenium_obj.request_interceptor = interceptor
    result = selenium_obj.request("GET", url)
    customization.RESP_HANDLER(result)

    extract_links(result.text, seed, selenium_obj)
    extract_links2(seed, selenium_obj)

    return result, cov_uuid

# crawl a link and get the test coverage of the request
def crawl_with_eval(link, seed, selenium_obj):
    result, cov_uuid = crawl_link(link, seed, selenium_obj)
    if result.status_code in config.DONT_CARE_STATUS_CODE:
        return False

    has_new_cov = cov.evaluate_cov(cov_uuid)
    # priority = prior.evaluate_prior(result)
    if has_new_cov:
        utils.REDIS_OBJ.sadd("url_seed", f"{link}%%{seed}")
        return True
    return False


import sys


def main(port_offset):
    try:
        global TARGET
        TARGET = f"localhost:{1194 + port_offset}"
        # init crawl
        utils.INFO("hsfuzz started")
        selenium_obj = get_selenium_obj()
        crawl_link("", 1, selenium_obj)
        utils.REDIS_OBJ.sadd("url_seed", f"%%1")
        print("Init finished")
        cov_count = 0
        while 1:
            link = get_link_from_redis()
            cter = 0
            while link is None:
                cter += 1
                if cter > 5:
                    sys.exit(0)
                utils.INFO("Waiting for links...")
                link = get_link_from_redis()
                time.sleep(config.WAIT_TIME)
            link = link.decode("latin-1")
            links = link.split("%%")
            m = mutator.Mutator(links[0], links[1])
            m.mutate()
            link, seed = m.to_url()
            if utils.REDIS_OBJ.hexists("already_crawled", f"{link}%%{seed}"):
                continue
            utils.DEBUG(f"Working on link {link}")
            crawl_with_eval(link, seed, selenium_obj)
    except:
        utils.ERROR(f"Chromium dead")
        main(port_offset)
