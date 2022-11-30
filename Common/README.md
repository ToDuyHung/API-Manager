# ServiceWrapper Package

## Introduction
This is a wrapper for any service in TMT-AI Ecosystem.   
This lib includes:
* 2 main interfaces: Kafka and RESTFul API
* Caching module for any fast retrieve results of any function of your code. 

## How to use

There are 2 examples in this package:
1. How to use base service object:   

_CODE FILE:_ 

    
    import time

    from services.base_service import BaseServiceSingleton, BaseServiceWithRAMCacheSingleton, BaseServiceWithCacheSingleton
    from config.config import Config


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
    
        def __call__(self, input_data):
            def request_func():
                time.sleep(5)
                return input_data
            output = self.make_request(request_func=request_func, key="some key", postfix="MayBe__call__")
            return output   

    if __name__ == "__main__":
    _config = Config(cache_socket_host="localhost",
                     cache_socket_port="8080",
                     cache_socket_endpoint="getdata")
    example_service = ExampleService(_config)
    example_ram_cache_service = ExampleWithRAMService(_config)
    example_cache_service = ExampleWithCacheService(_config)
    time.sleep(5)

    a = time.time()
    print(example_service("hello_world"))
    print("NO RAM CACHE -> sleep 10s every request", time.time() - a)

    for i in range(5):
        a = time.time()
        print(example_ram_cache_service("hello_world"))
        print("RAM CACHE -> sleep 10s first request and then no sleep with the same key", time.time() - a)

    for i in range(5):
        a = time.time()
        print(example_cache_service("hello_world"))
        print("EXTERNAL CACHE SERVICE -> no sleep every time with the same key", time.time() - a)


_OUTPUTS:_   

    hello_world
    NO RAM CACHE -> sleep 10s every request 5.007730960845947
    hello_world
    RAM CACHE -> sleep 10s first request and then no sleep with the same key 5.014838457107544
    hello_world
    RAM CACHE -> sleep 10s first request and then no sleep with the same key 0.0
    hello_world
    RAM CACHE -> sleep 10s first request and then no sleep with the same key 0.0
    hello_world
    RAM CACHE -> sleep 10s first request and then no sleep with the same key 0.0
    hello_world
    RAM CACHE -> sleep 10s first request and then no sleep with the same key 0.0
    hello_world
    EXTERNAL CACHE SERVICE -> no sleep every time with the same key 0.011059284210205078
    hello_world
    EXTERNAL CACHE SERVICE -> no sleep every time with the same key 0.0
    hello_world
    EXTERNAL CACHE SERVICE -> no sleep every time with the same key 0.0
    hello_world
    EXTERNAL CACHE SERVICE -> no sleep every time with the same key 0.0
    hello_world
    EXTERNAL CACHE SERVICE -> no sleep every time with the same key 0.0

This BaseService give you a common caching service via self.make_request function. 

2. How to use default interfaces object:  
You can run _app.py_ OR the following code:


    from utils.utils import setup_logging
    from config.config import Config
    from Common.singleton import BaseSingleton
    from interfaces.restful.api_app import APIApp
    from interfaces.kafka.kafka_app import KafkaApp
    from pipeline.base_pipeline import BasePipeline
    from services.monitor import Monitor
    
    
    class App(BaseSingleton):
        def __init__(self, config: Config = None):
            super(App, self).__init__()
            self.logger = logging.getLogger(self.__class__.__name__)
            self.config = config if config is not None else Config()
            self.pipeline = BasePipeline(config)
            self.pipeline.add
            self.api_app = APIApp(config)
            self.kafka_app = KafkaApp(config)
            self.monitor = Monitor(config)
    
        def start(self):
            self.kafka_app.start()
            self.monitor.start()
            self.api_app.start()
    
        def join(self):
            self.kafka_app.join()
            self.monitor.join()
    
    
    if __name__ == "__main__":
        _config = Config(kafka_consume_topic = 'baseService.test'
                        kafka_publish_topic = 'baseService'
                        kafka_bootstrap_servers = '172.29.13.24:35000'
                        kafka_auto_offset_reset = 'earliest'
                        kafka_group_id = 'baseService'
                        api_host = "0.0.0.0"
                        api_port = 8080)
        app = App(_config)
        app.pipeline.add_process_func(lambda x: x)
        app.start()
        app.join()

# Value Parsing

## Time, DATE, TIME, ...
Some processed format of datetime entity => parse to dd/mm/YYYY format

- dd/mm/YYYY, dd/mm, mm/YYYY, ...
  - 25/5, tháng 6/2022, ...
- DayOfWeek
  - thứ 2, thứ 3, ...
  - thứ 4 tuần sau, ...
- n+ more days, months, ...
  - ngày mai, ngày mốt, ...
  - 2 tháng tới, 2 ngày nữa
- specific day in next month or n+ months
  - ngày 15 tháng sau