import logging
from abc import ABC
from queue import Queue
from threading import Thread, Event
import binascii
import zlib
import time
import json
from urllib.parse import quote
from uuid import uuid5, uuid4

from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.utils.data_utils import jaccard_distance, text_ngram
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.ServiceWrapper.services.stomp_socket.client import Client


class Cache:
    def __init__(self, config: Config = None, name: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.name = name if name is not None else self.__class__.__name__
        self.storage = {}

    def __getitem__(self, item):
        return self.storage.get(item)

    def __delitem__(self, key):
        if key in self.storage:
            del self.storage[key]

    def __contains__(self, item):
        return item in self.storage

    def __setitem__(self, key, value):
        raise NotImplementedError("Need Implementation")

    def size(self) -> int:
        raise NotImplementedError("Need Implementation")

    def get_remove_key(self):
        raise NotImplementedError("Need Implementation")

    def drop(self):
        if self.size() >= self.config.max_ram_cache_size:
            remove_key = self.get_remove_key()
            del self[remove_key]
            self.logger.info(f"REMOVE key [{remove_key}] from cache [{self.name}]")
            print(f"REMOVE key [{remove_key}] from cache [{self.name}]. {self.size()}/{self.config.max_ram_cache_size}")

    def clear(self):
        raise NotImplementedError("Need Implementation")

    @staticmethod
    def get_cache(config: Config = None, name: str = None):
        cache_type = config.cache_type
        if cache_type == "FIFO":
            return FIFOCache(config=config, name=name)
        elif cache_type == "LRU":
            return LRUCache(config=config, name=name)


class FIFOCache(Cache, ABC):
    def __init__(self, config: Config = None, name: str = None):
        super(FIFOCache, self).__init__(config=config, name=name)
        self.queue = Queue(maxsize=self.config.max_ram_cache_size)
        self.storage = {}

    def __setitem__(self, key, value):
        if key not in self.storage:
            self.queue.put(key)
            self.drop()
        self.storage[key] = value

    def size(self):
        return self.queue.qsize()

    def get_remove_key(self):
        return self.queue.get()

    def clear(self):
        self.storage = {}
        old_queue = self.queue
        self.queue = Queue(maxsize=self.config.max_ram_cache_size)
        while old_queue.qsize() > 0:
            old_queue.get()


class LRUCache(Cache, ABC):

    def __init__(self, config: Config = None, name: str = None):
        super(LRUCache, self).__init__(config=config, name=name)
        self.timer = {}
        self.key_list = []
        self.count = 0

    def sort_key_list(self):
        self.key_list.sort(key=lambda item: self.timer[item], reverse=True)

    def __contains__(self, item):
        output = item in self.storage
        if output:
            self.timer[item] = time.time()
            self.sort_key_list()
        return output

    def __getitem__(self, item):
        output = self.storage.get(item)
        self.timer[item] = time.time()
        self.sort_key_list()
        return output

    def __delitem__(self, key):
        if key in self.storage:
            del self.storage[key]
            del self.timer[key]

    def __setitem__(self, key, value):
        if key not in self.storage:
            self.key_list.append(key)
        self.timer[key] = time.time()
        self.storage[key] = value
        self.sort_key_list()
        self.drop()
        self.logger.info(f"ADD key [{key}]")

    def size(self):
        return len(self.key_list)

    def get_remove_key(self):
        return self.key_list.pop(-1)

    def clear(self):
        self.storage = {}
        self.timer = {}
        self.key_list = []


class BaseCacheService(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(BaseCacheService, self).__init__(config=config)
        self.search_times = []
        self.write_times = []

    @staticmethod
    def generate_request_id(key):
        return str(uuid5(uuid4(), key))

    @staticmethod
    def compress(data):
        data_string = json.dumps(data, ensure_ascii=False)
        output = binascii.hexlify(zlib.compress(data_string.encode(encoding="utf8"))).decode('utf-8')
        return output

    @staticmethod
    def decompress(data_string):
        data_string = str(zlib.decompress(bytes.fromhex(data_string)).decode(encoding="utf8"))
        return json.loads(data_string)

    @property
    def connected(self):
        raise NotImplementedError("Need Implementation")

    def save(self, key: str, data):
        raise NotImplementedError("Need Implementation")

    def search_func(self, key, size=5):
        raise NotImplementedError("Need Implementation")

    @property
    def search_per_second(self):
        return len(self.search_times) / sum(self.search_times)

    @property
    def save_per_second(self):
        return len(self.write_times) / sum(self.write_times)

    @property
    def info(self):
        return f"SEARCH_PER_SECOND: {self.search_per_second} items/s\n" \
               f"SAVE_PER_SECOND: {self.save_per_second} items/s"

    @staticmethod
    def get_best_result(text, candidates, exact=False):
        if len(candidates) > 0:
            if exact:
                candidates = [item for item in candidates if item["key"] == text]
                return candidates[0] if len(candidates) > 0 else None
            else:
                src_set = text_ngram(text, 3, c_mode=True)
                scores = [(item, jaccard_distance(src_set, text_ngram(item["key"], 3, c_mode=True)))
                          for item in candidates]
                scores.sort(key=lambda item: item[1], reverse=True)
                candidate, score = scores[0]
                if score >= 0.9:
                    return candidate

    def search(self, text, size=5, exact=False, pre_check_func=None):
        outputs = self.search_func(size=size, key=text)
        if outputs is not None:
            self.logger.info(f"Loaded results from ES Cache")
            if pre_check_func is not None:
                new_outputs = []
                key = text
                for output in outputs:
                    output_key = output["key"]
                    is_valid, key, candidate_key = pre_check_func(text, output_key)
                    if is_valid:
                        output["key"] = candidate_key
                        new_outputs.append(output)
                outputs = new_outputs
                text = key
            output = self.get_best_result(text, outputs, exact)
            if output is not None:
                return output["data"]
            return output
        return outputs

    @staticmethod
    def get_cache(config: Config = None):
        cache_endpoint_type = config.cache_endpoint_type
        if cache_endpoint_type == "socket":
            return SocketCacheService(config=config)
        else:
            return RestFulCacheService(config=config)


class SocketCacheService(BaseCacheService):
    def __init__(self, config: Config = None):
        super(SocketCacheService, self).__init__(config=config)
        self.client = None
        self.storage = {}
        self.search_times = []
        self.write_times = []
        self.init_worker = None
        self.init_client()

    @property
    def connected(self):
        if self.client is not None:
            return self.client.connected
        else:
            return False

    def init_client(self):
        def init_job():
            while True:
                if self.client is None or not self.client.connected:
                    try:
                        self.client = Client(host=self.config.cache_host,
                                             port=self.config.cache_port,
                                             endpoint=self.config.cache_endpoint)
                        self.client.auto_subscribe("/cache/get/", self._process_data)
                    except Exception as e:
                        print("CANNOT INIT CLIENT", e)
                time.sleep(1)
        self.init_worker = Thread(target=init_job, daemon=True)
        self.init_worker.start()

    @staticmethod
    def generate_request_id(key):
        return str(uuid5(uuid4(), key))

    def send(self, data: dict):
        if self.client is None or not self.client.connected:
            self.client = None
            self.logger.info("Cannot send message. WAIT FOR CONNECTION")
            print("Cannot send message. WAIT FOR CONNECTION")
            return False
        else:
            try:
                self.client.send(f"/app/{self.config.cache_endpoint}",
                                 body={"userId": self.client.client_id, "data": data})
                return True
            except Exception as e:
                self.logger.error(f"Cannot send data to socket. Error: {e}")
                return False

    def save(self, key: str, data):
        if self.client is None or not self.client.connected:
            return
        start_time = time.time()
        done_event = Event()
        done_event.clear()
        request_id = self.generate_request_id(key)
        data = self.compress(data)
        save_data = {"key": key, "data": data, "requestId": request_id}
        self.storage[request_id] = {
            "event": done_event,
            "data": None
        }
        success = self.send(save_data)
        done_event.wait(1)
        if success:
            if done_event.is_set():
                del self.storage[request_id]
                self.write_times.append(time.time() - start_time)
                while len(self.write_times) > 60:
                    self.write_times.pop(0)
        else:
            del self.storage[request_id]

    def search_func(self, key, size=5):
        if self.client is None or not self.client.subscribed:
            return
        start_time = time.time()
        done_event = Event()
        done_event.clear()
        request_id = self.generate_request_id(key)
        search_data = {"searchKey": key, "requestId": request_id, "size": size}
        self.storage[request_id] = {
            "event": done_event,
            "data": None
        }
        self.send(search_data)
        done_event.wait(1)
        out = None
        if done_event.is_set():
            out = self.storage[request_id]["data"]
            del self.storage[request_id]
        if out is not None:
            self.search_times.append(time.time() - start_time)
            while len(self.search_times) > 60:
                self.search_times.pop(0)
            out = out["data"]
            if out is None:
                out = []
            else:
                for item in out:
                    item["data"] = self.decompress(item["data"])
        return out

    def _process_data(self, frame):
        try:
            text_data = frame.body
            while '\\"' in text_data:
                text_data = text_data.replace('\\"', '"')
            data = json.loads(text_data)
            request_id = data["requestId"]
            if request_id in self.storage:
                del data["requestId"]
                self.storage[request_id]["data"] = data
                self.storage[request_id]["event"].set()
        except Exception as e:
            self.logger.error(f"Error parsing data from socket. Error: {e}")

    @property
    def search_per_second(self):
        return len(self.search_times) / sum(self.search_times)

    @property
    def save_per_second(self):
        return len(self.write_times) / sum(self.write_times)

    @property
    def info(self):
        return f"SEARCH_PER_SECOND: {self.search_per_second} items/s\n" \
               f"SAVE_PER_SECOND: {self.save_per_second} items/s"


class RestFulCacheService(BaseCacheService):
    def __init__(self, config: Config = None):
        super(RestFulCacheService, self).__init__(config=config)
        self.search_times = []
        self.write_times = []
        self.api_url = f"http://{config.cache_host}:{config.cache_port}/{config.cache_endpoint}"

    @property
    def connected(self):
        return True

    def save(self, key: str, data):
        def save_request(item):
            save_data = {"key": key, "data": item}
            output = self.session.post(self.api_url, json=save_data).json()
            return output

        start_time = time.time()
        data = self.compress(data)
        self.make_request(lambda: save_request(data), num_retry=1)
        self.write_times.append(time.time() - start_time)

    def search_func(self, key, size=5):
        def search_request():
            url_key = quote(key, safe='')
            output = self.session.get(f"{self.api_url}{url_key}").json()
            return output

        start_time = time.time()
        out = self.make_request(search_request, num_retry=1)
        if out is not None:
            self.search_times.append(time.time() - start_time)
            while len(self.search_times) > 60:
                self.search_times.pop(0)
            out = out["data"]
            if out is None:
                out = []
            else:
                for item in out:
                    item["data"] = self.decompress(item["data"])
        return out


