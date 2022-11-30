import json
import logging
from threading import Thread

from kafka import KafkaConsumer, KafkaProducer

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.singleton import Singleton
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.ServiceWrapper.services.buffer_manager import BufferManager


class MessageManager(metaclass=Singleton):
    def __init__(self, config: Config = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.consumer = None
        self.producer = None
        self.buffer_manager = BufferManager()
        self.buffer_manager.create_buffer(INPUT_BUFFER, max_size=2)
        self.buffer_manager.create_buffer(OUTPUT_BUFFER)
        self.consumer_worker = Thread(target=self.consumer_job, daemon=True)
        self.producer_worker = Thread(target=self.producer_job, daemon=True)
        self.create_success = False
        self.create_kafka_channels()

    def create_kafka_channels(self):
        try:
            self.consumer = KafkaConsumer(self.config.kafka_consume_topic,
                                          bootstrap_servers=self.config.kafka_bootstrap_servers,
                                          auto_offset_reset=self.config.kafka_auto_offset_reset,
                                          group_id=self.config.kafka_group_id)
            self.producer = KafkaProducer(bootstrap_servers=self.config.kafka_bootstrap_servers)
            self.logger.info(f"Kafka channels create successfully. "
                             f"\nIN: {self.config.kafka_consume_topic} "
                             f"\nOUT: {self.config.kafka_publish_topic}")
            self.create_success = True
        except Exception as e:
            self.logger.error(f"Cannot create Kafka Channels. Error: {e}")
            self.create_success = False

    def start(self):
        self.consumer_worker.start()
        self.producer_worker.start()

    def consumer_job(self):
        self.logger.info("START MESSAGE CONSUMER")
        while True:
            try:
                for message in self.consumer:
                    try:
                        message = message.value.decode('ascii')
                        message = message.replace("'", '"')
                        message = json.loads(message)
                        data = BaseDataModel.from_json(message)
                        self.logger.info(f'INPUT MESSAGE: {message["index"]}')
                        self.buffer_manager.put_data(buffer_name=INPUT_BUFFER, data=data)
                    except Exception as e:
                        self.logger.error(f'Input Message Error: {e}')
            except Exception as e:
                self.logger.error(f'Input Message Error: {e}')
                self.create_kafka_channels()

    def producer_job(self):
        while True:
            try:
                data: BaseDataModel = self.buffer_manager.get_data(buffer_name=OUTPUT_BUFFER, timeout=60)
                if data is None:
                    continue
                data.update_response_time()
                self.producer.send(self.config.kafka_publish_topic, value=json.dumps(data.dict()).encode('utf-8'))
                self.logger.debug(f'SUCCESS PUT RESULT: {data.index}')
            except Exception as e:
                self.logger.debug(f'ERROR WHEN PUT RESULT: {e}')

    def join(self):
        self.consumer_worker.join()
        self.producer_worker.join()
