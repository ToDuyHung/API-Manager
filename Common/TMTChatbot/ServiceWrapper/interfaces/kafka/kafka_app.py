from TMTChatbot.Common.config.config import Config
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.ServiceWrapper.pipeline.base_pipeline import BasePipeline
from TMTChatbot.ServiceWrapper.interfaces.kafka.message_manager import MessageManager


class KafkaApp(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(KafkaApp, self).__init__(config=config)
        self.message_manager = MessageManager(config=config)
        if self.message_manager.create_success:
            self.create_success = True
            self.process_pipeline = BasePipeline(config=config)
            self.logger.info(f"{self.__class__.__name__} create successfully")
        else:
            self.create_success = False
            self.process_pipeline = None
            self.logger.info(f"{self.__class__.__name__} create FAILED")

    def start(self):
        if self.create_success:
            self.message_manager.start()
            self.process_pipeline.start()
            self.logger.info("KAFKA APP STARTED")

    def join(self):
        if self.create_success:
            self.message_manager.join()
            self.process_pipeline.join()
            self.logger.info("KAFKA APP STOPPED")

