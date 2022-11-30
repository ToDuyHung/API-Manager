import time

from TMTChatbot.ServiceWrapper.services.base_service import (
    BaseServiceSingleton
)
from TMTChatbot.ServiceWrapper.services.base_cache_service import (
    BaseServiceWithRAMCacheSingleton,
    BaseServiceWithCacheSingleton
)
from TMTChatbot.Common.config.config import Config


class ExampleService(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(ExampleService, self).__init__(config)

    def __call__(self, input_data):
        def request_func():
            time.sleep(5)
            return input_data
        output = self.make_request(request_func=request_func, key="some key", postfix="MayBe__call__")
        return output


class ExampleWithRAMService(BaseServiceWithRAMCacheSingleton):
    def __init__(self, config: Config = None):
        super(ExampleWithRAMService, self).__init__(config)

    def __call__(self, input_data):
        def request_func():
            time.sleep(5)
            return input_data
        output = self.make_request(request_func=request_func, key="some key", postfix="MayBe__call__")
        return output


class ExampleWithCacheService(BaseServiceWithCacheSingleton):
    def __init__(self, config: Config = None):
        super(ExampleWithCacheService, self).__init__(config)

    def __call__(self, input_data, key="some key"):
        def request_func():
            time.sleep(5)
            return input_data
        output = self.make_request(request_func=request_func, key=key, postfix="MayBe__call__")
        return output


if __name__ == "__main__":
    import numpy as np
    _config = Config(cache_socket_host="localhost",
                     cache_socket_port="8080",
                     cache_socket_endpoint="getdata")
    # example_service = ExampleService(_config)
    # example_ram_cache_service = ExampleWithRAMService(_config)
    example_cache_service = ExampleWithCacheService(_config)
    time.sleep(5)

    # a = time.time()
    # print(example_service("hello_world"))
    # print("NO RAM CACHE -> sleep 10s every request", time.time() - a)
    #
    # for i in range(5):
    #     a = time.time()
    #     print(example_ram_cache_service("hello_world"))
    #     print("RAM CACHE -> sleep 10s first request and then no sleep with the same key", time.time() - a)

    data = np.array([np.e] * 768)
    for i in range(10):
        a = time.time()
        _key = f"e_value_{i}"
        _output = example_cache_service(input_data=data.tolist(), key=_key)
        # print(np.sum(np.array(_output) - data))
        # print("EXTERNAL CACHE SERVICE -> no sleep every time with the same key", time.time() - a)



