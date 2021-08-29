import time
from urllib.parse import urlparse, urlunparse, ParseResult
from urllib.parse import urlencode, unquote
import sys
import random

import utils
import config


class Mutator:
    current_args_str = {}
    current_args_num = {}
    keys_str = []
    keys_num = []
    url_obj = ""
    cter = 0
    seed = 0

    @staticmethod
    def __is_number(v: str):
        v = unquote(v)
        try:
            int(v)
            return True
        except ValueError:
            try:
                float(v)
                return True
            except ValueError:
                return False

    def __init__(self, url: str, seed: int):
        self.url_obj = urlparse(url)
        url_query = self.url_obj.query
        for i in url_query.split("&"):
            try:
                k, v = i.split("=")
            except ValueError:
                continue
            if not self.__is_number(v):
                self.current_args_str[unquote(k)] = unquote(v)
            else:
                try:
                    self.current_args_num[unquote(k)] = int(unquote(v))
                except ValueError:
                    self.current_args_num[unquote(k)] = float(unquote(v))
                except Exception as e:
                    utils.ERROR(f"Failed to unserialize float {unquote(v)} due to {e}")
        self.keys_str = [x for x in self.current_args_str]
        self.keys_num = [x for x in self.current_args_num]
        self.seed = seed

    def to_url(self):
        arg_str = ""
        arg_str += urlencode({**self.current_args_str, **self.current_args_num})
        return urlunparse(
            ParseResult(scheme='', netloc='',
                        path=self.url_obj.path,
                        params=self.url_obj.params,
                        query=arg_str[:-1] if len(arg_str) > 0 else "",
                        fragment='')), self.seed

    # mutators
    def _flip_value(self, seed: int):
        if len(self.keys_num) == 0:
            return self.mutate()

        k = seed % len(self.keys_num)
        value = 0 - self.current_args_num[self.keys_num[k]]
        self.current_args_num[self.keys_num[k]] = value
        return True

    def _overflow(self, seed: int):
        if len(self.keys_num) == 0:
            return self.mutate()

        k = seed % len(self.keys_num)
        self.current_args_num[self.keys_num[k]] = 2 << 30 + 1 \
            if seed % 2 == 0 else -2 << 30 - 1
        return True

    def _rand_value(self, seed: int):
        if len(self.keys_num) == 0:
            return self.mutate()

        k = seed % len(self.keys_num)
        self.current_args_num[self.keys_num[k]] = random.random() if seed % 2 == 0\
            else random.randint(0 - (2 << 30), 2 << 30)
        return True

    def _add_str(self, seed: int):
        if len(self.keys_str) == 0:
            return self.mutate()

        k = seed % len(self.keys_str)
        value = self.current_args_str[self.keys_str[k]]
        if len(value) == 0:
            return self.mutate()

        value = value[:seed % len(value)] + chr(seed % sys.maxunicode) + \
            value[seed % len(value):]
        self.current_args_str[self.keys_str[k]] = value
        return True

    def _update_str(self, seed: int):
        if len(self.keys_str) == 0:
            return self.mutate()

        k = seed % len(self.keys_str)
        value = self.current_args_str[self.keys_str[k]]

        if len(value) == 0:
            return self.mutate()

        value = value[:seed % len(value)] + chr(seed % sys.maxunicode) + \
            value[seed % len(value) + 1:]
        self.current_args_str[self.keys_str[k]] = value
        return True

    def _remove_str(self, seed: int):
        if len(self.keys_str) == 0:
            return self.mutate()

        k = seed % len(self.keys_str)
        value = self.current_args_str[self.keys_str[k]]

        if len(value) == 0:
            return self.mutate()

        value = value[seed % len(value) + 1:] + value[:seed % len(value)]
        self.current_args_str[self.keys_str[k]] = value
        return True

    def _remove_key(self, seed: int):

        if seed % 2 == 0:
            if len(self.keys_str) == 0:
                return self.mutate()
            key = self.keys_str[seed % len(self.keys_str)]
            del self.keys_str[seed % len(self.keys_str)]
            del self.current_args_str[key]
        else:
            if len(self.keys_num) == 0:
                return self.mutate()
            key = self.keys_num[seed % len(self.keys_num)]
            del self.keys_num[seed % len(self.keys_num)]
            del self.current_args_num[key]
        return True

    def _change_seed(self, seed: int):
        self.seed = seed
        return True

    # noinspection PyArgumentList
    def mutate(self):
        registered_mutators = [
            self._flip_value,
            self._overflow,
            self._rand_value,
            self._add_str,
            self._update_str,
            self._remove_str,
            self._remove_key,
            self._change_seed
        ]
        self.cter += 1
        if self.cter > 3:
            return False
        # log.DEBUG(f"State: {self.current_args_str} {self.current_args_num} {self.keys_str} {self.keys_num}")
        return random.choice(registered_mutators)(
            seed=random.randint(0 - (2 << 30), 2 << 30)
        )
