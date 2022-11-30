from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.singleton import Singleton
from TMTChatbot.Common.utils.data_utils import remove_accents
from TMTChatbot.ServiceWrapper.services.base_service import BaseService, BaseAsyncService
from TMTChatbot.ServiceWrapper.services.cache import Cache, BaseCacheService


class BaseServiceWithRAMCache(BaseService):
    def __init__(self, config: Config = None):
        super(BaseServiceWithRAMCache, self).__init__(config=config)
        self.cache = Cache.get_cache(config=config, name=self.__class__.__name__)

    def clear_cache(self):
        self.cache.clear()

    @staticmethod
    def extract_key(template_key):
        class_name, template_key = template_key.split("*@")
        class_name = class_name.replace("@", "").strip()
        key, postfix = template_key.split("*#")
        key = key.replace("#", "").strip()
        postfix = postfix.replace("*&", "").replace("&", "").strip()
        return class_name, key, postfix

    def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                     num_retry: int = None):
        if key is None:
            return super().make_request(request_func, call_back_func, num_retry=num_retry)

        key = remove_accents(key)
        key = self.generate_cache_key(key, postfix)

        if key in self.cache and self.get_prop() >= call_prop:
            return self.cache[key]
        else:
            result = super().make_request(request_func, call_back_func, num_retry=num_retry)
            if result is not None:
                self.cache[key] = result
            return result


class BaseAsyncServiceWithRAMCache(BaseAsyncService, BaseServiceWithRAMCache):
    def __init__(self, config: Config = None):
        BaseAsyncService.__init__(self, config=config)
        BaseServiceWithRAMCache.__init__(self, config=config)

    async def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                           num_retry: int = None):
        if key is None:
            return await super().make_request(request_func, call_back_func, num_retry=num_retry)

        key = remove_accents(key)
        key = self.generate_cache_key(key, postfix)

        if key in self.cache and self.get_prop() >= call_prop:
            return self.cache[key]
        else:
            result = await super().make_request(request_func, call_back_func, num_retry=num_retry)
            if result is not None:
                self.cache[key] = result
            return result


class BaseServiceWithCache(BaseServiceWithRAMCache):
    def __init__(self, config: Config = None):
        super(BaseServiceWithCache, self).__init__(config=config)
        self.cache_service = BaseCacheService.get_cache(config=config)

    def pre_check_key(self, query_key=None, candidate=None):
        class_name, key, postfix = self.extract_key(query_key)
        candidate_class_name, candidate_key, candidate_postfix = self.extract_key(candidate)
        return candidate_class_name == class_name and postfix == candidate_postfix, key, candidate_key

    def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                     num_retry: int = None):
        if key is None:
            return super().make_request(request_func, call_back_func, num_retry=num_retry)

        key = remove_accents(key)
        key = self.generate_cache_key(key, postfix)

        if key in self.cache and self.get_prop() >= call_prop:
            # self.logger.info(f"GET key [{key}] from cache [{self.__class__.__name__}]")
            return self.cache[key]
        else:
            result = self.cache_service.search(key, pre_check_func=self.pre_check_key, exact=True)
            if result is not None:
                self.cache[key] = result
                return result
            else:
                result = super().make_request(request_func, call_back_func, num_retry=num_retry)
                if result is not None:
                    self.cache[key] = result
                    self.cache_service.save(key=key, data=result)
                return result


class BaseAsyncServiceWithCache(BaseAsyncServiceWithRAMCache, BaseServiceWithCache):
    def __init__(self, config: Config = None):
        BaseAsyncServiceWithRAMCache.__init__(self, config=config)
        BaseServiceWithCache.__init__(self, config=config)

    async def make_request(self, request_func, call_back_func=None, key=None, postfix="", call_prop: float = 0,
                           num_retry: int = None):
        if key is None:
            return await super().make_request(request_func, call_back_func, num_retry=num_retry)

        key = remove_accents(key)
        key = self.generate_cache_key(key, postfix)

        if key in self.cache and self.get_prop() >= call_prop:
            # self.logger.info(f"GET key [{key}] from cache [{self.__class__.__name__}]")
            return self.cache[key]
        else:
            result = self.cache_service.search(key, pre_check_func=self.pre_check_key, exact=True)
            if result is not None:
                self.cache[key] = result
                return result
            else:
                result = await super().make_request(request_func, call_back_func, num_retry=num_retry)
                if result is not None:
                    self.cache[key] = result
                    self.cache_service.save(key=key, data=result)
                return result


class BaseServiceWithCacheSingleton(BaseServiceWithCache, metaclass=Singleton):
    pass


class BaseServiceWithRAMCacheSingleton(BaseServiceWithRAMCache, metaclass=Singleton):
    pass


class BaseAsyncServiceWithCacheSingleton(BaseAsyncServiceWithCache, metaclass=Singleton):
    pass
