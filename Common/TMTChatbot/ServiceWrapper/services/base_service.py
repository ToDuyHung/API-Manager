import logging
import numpy as np
import asyncio
import aiohttp

import requests
import time

from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Common.config.config import Config


class BaseService:
    def __init__(self, config: Config = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.session = None
        self.logger.info(f"CREATE {self.__class__.__name__}")

    def get_func(self, func_name: str):
        return getattr(self, func_name)

    def init_session(self, force=False):
        if self.session is None or force:
            self.session = requests.session()

    def call_back_func(self):
        self.init_session(True)

    @staticmethod
    def get_prop():
        return np.random.uniform(0, 1)

    def generate_cache_key(self, key: str, postfix: str = ""):
        return f"@{self.__class__.__name__}*@ #{key}*# &{postfix}*&"

    @staticmethod
    async def wait(job, *args):
        if asyncio.iscoroutinefunction(job):
            output = await job()
        else:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(None, job, *args)
        return output

    def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                     num_retry: int = None):
        """
        This is the common make request function with try cache mechanism
        :param call_prop: probability that the <request_func> is recall even if <key> exists in cache
        :param request_func: a function that need to process. No args can be passed to this function
        :param call_back_func: function to process if request_func return error
        :param key: cache the result with this key. Key is only needed when using Cache BaseServices
        :param postfix: tell where key to be stored in cache space
        :param num_retry: number of retry if a request fail
        :return: the output of request_func
        """
        self.init_session(False)
        result = None
        retry = num_retry if num_retry is not None else self.config.num_retry
        while result is None and retry > 0:
            try:
                result = request_func()
            except Exception as e:
                self.logger.error(
                    f"[{self.__class__.__name__}]. Cannot make request. Retry remains: {retry}. Error : {e}")
                print(
                    f"[{self.__class__.__name__}]. Cannot make request. Retry remains: {retry}. Error : {e}")
                if call_back_func is not None:
                    call_back_func()
                else:
                    self.call_back_func()
                retry -= 1
                if retry > 0:
                    time.sleep(0.1)
        return result


class BaseAsyncService(BaseService):

    async def call_back_func(self):
        await self.init_session(True)

    async def init_session(self, force=False):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        elif force:
            await self.session.close()
            self.session = aiohttp.ClientSession()

    async def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                           num_retry: int = None):
        """
        This is the common make request function with try cache mechanism
        :param call_prop: probability that the <request_func> is recall even if <key> exists in cache
        :param request_func: a function that need to process. No args can be passed to this function
        :param call_back_func: function to process if request_func return error
        :param key: cache the result with this key. Key is only needed when using Cache BaseServices
        :param postfix: tell where key to be stored in cache space
        :param num_retry: number of retry if a request fail
        :return: the output of request_func
        """
        await self.init_session(False)
        result = None
        retry = num_retry if num_retry is not None else self.config.num_retry
        while result is None and retry > 0:
            try:
                result = await request_func()
            except Exception as e:
                self.logger.error(f"[{self.__class__.__name__}]. Cannot make request. Retry remains: {retry}. "
                                  f"Error : {e}")
                if call_back_func is not None:
                    if asyncio.iscoroutinefunction(call_back_func):
                        await call_back_func()
                    else:
                        call_back_func()
                else:
                    if asyncio.iscoroutinefunction(self.call_back_func):
                        await self.call_back_func()
                    else:
                        raise ValueError("self.call_back_func must be async function")
                retry -= 1
                if retry > 0:
                    await asyncio.sleep(0.1)
        return result


class BaseServiceSingleton(BaseService, BaseSingleton):
    pass


class BaseAsyncServiceSingleton(BaseAsyncService, BaseSingleton):
    pass

