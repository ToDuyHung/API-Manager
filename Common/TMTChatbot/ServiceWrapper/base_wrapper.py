import logging

from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Common.utils.logging_utils import setup_logging
from TMTChatbot.ServiceWrapper.interfaces.restful.api_app import APIApp
from TMTChatbot.ServiceWrapper.interfaces.kafka.kafka_app import KafkaApp
from TMTChatbot.ServiceWrapper.pipeline.base_pipeline import BasePipeline
from TMTChatbot.ServiceWrapper.services.monitor import Monitor


class BaseApp(BaseSingleton):
    def __init__(self, config: Config = None, with_kafka_app: bool = True, with_api_app: bool = True,
                 with_default_pipeline: bool = True):
        super(BaseApp, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.with_default_pipeline = with_default_pipeline
        self.with_kafka_app = with_kafka_app
        self.with_api_app = with_api_app
        if with_default_pipeline:
            self.pipeline = BasePipeline(config)
        else:
            self.pipeline = None
        if with_api_app:
            self.api_app = APIApp(config)
        if with_kafka_app:
            self.kafka_app = KafkaApp(config)
        self.monitor = Monitor(config)

    def add_process_function(self, func):
        if self.pipeline is not None:
            self.pipeline.add_process_func(func)
        else:
            raise ValueError("Need a pipeline implementation")

    def start(self, n_workers: int = 1):
        if self.with_kafka_app:
            self.kafka_app.start()
        self.monitor.start()
        if self.with_api_app:
            self.api_app.start(n_workers=n_workers)

    def join(self):
        if self.with_kafka_app:
            self.kafka_app.join()
        self.monitor.join()


if __name__ == "__main__":
    _config = Config()
    setup_logging(logging_folder=_config.logging_folder, log_name=_config.log_name)
    app = BaseApp(_config)
    app.start()
    app.join()

