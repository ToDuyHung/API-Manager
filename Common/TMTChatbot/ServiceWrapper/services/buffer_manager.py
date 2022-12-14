import logging
from queue import Queue
import json

from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Common.singleton import BaseSingleton


class BufferManager(BaseSingleton):

    def __init__(self, config: Config = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.buffers = {}

    def create_buffer(self, buffer_name: str, max_size=1):
        if buffer_name in self.buffers:
            self.logger.warning(f"{buffer_name} already exists => Choose another buffer name")
        else:
            self.buffers[buffer_name] = Queue(maxsize=max_size)
            self.logger.info(f"INIT BUFFER {buffer_name} as TQueue")

    def get_data(self, buffer_name: str, timeout=10):
        if buffer_name in self.buffers:
            try:
                data: BaseDataModel = self.buffers[buffer_name].get(timeout=timeout)
                self.logger.debug(f"GET ITEM FROM {buffer_name}. {self.buffers[buffer_name].qsize()} ITEMS REMAINS")
                return data
            except Exception as e:
                self.logger.warning(f"Get data timeout. Error: {e}")
        else:
            raise ValueError(f"Buffer name {buffer_name} not in Buffer list: {list(self.buffers.keys())}")

    def put_data(self, buffer_name: str, data: BaseDataModel):
        if buffer_name in self.buffers:
            self.buffers[buffer_name].put(data)
            self.logger.debug(f"PUT ITEM TO {buffer_name}. {self.buffers[buffer_name].qsize()} ITEMS REMAINS")
        else:
            raise ValueError(f"Buffer name {buffer_name} not in Buffer list: {list(self.buffers.keys())}")

    @property
    def info(self):
        return json.dumps({q_name: self.buffers[q_name].qsize() for q_name in self.buffers}, indent=4)
