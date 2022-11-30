from time import sleep
from threading import Thread
from TMTChatbot.Common.config.config import Config
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.ServiceWrapper.services.buffer_manager import BufferManager
from TMTChatbot.ServiceWrapper.pipeline.base_pipeline import BasePipeline


class Monitor(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(Monitor, self).__init__(config=config)
        self.worker = Thread(target=self.monitor, daemon=True)
        self.monitor_items = {}
        self.add_monitor_service(BufferManager())
        self.add_monitor_service(BasePipeline(config))

    def add_monitor_service(self, service):
        self.monitor_items[service.__class__.__name__] = service

    def monitor(self):
        while True:
            output = "["
            for item_name, item in self.monitor_items.items():
                output += f"\t- {item_name}: {item.info}\n"
            output += "]"
            self.logger.info("MONITOR:\n" + output)
            sleep(60)

    def start(self):
        self.worker.start()

    def join(self):
        self.worker.join()
