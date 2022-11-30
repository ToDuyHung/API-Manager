import os

from common.common_keys import *
from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.config.config import Config as BaseConfig


class Config(BaseConfig):
    def __init__(self,
                 mongo_host=os.getenv(MONGO_HOST, "172.29.13.24"),
                 mongo_port=os.getenv(MONGO_PORT, 20253),
                 mongo_username=os.getenv(MONGO_USERNAME, "admin"),
                 mongo_password=os.getenv(MONGO_PASSWORD, "admin")):
        super(Config, self).__init__(
            kafka_consume_topic=os.getenv(KAFKA_CONSUME_TOPIC, 'message'),
            kafka_publish_topic=os.getenv(KAFKA_PUBLISH_TOPIC, 'shop_message'),
            kafka_bootstrap_servers=os.getenv(KAFKA_BOOTSTRAP_SERVERS, '172.29.13.24:35000'),
            kafka_auto_offset_reset=os.getenv(KAFKA_AUTO_OFFSET_RESET, 'earliest'),
            kafka_group_id=os.getenv(KAFKA_GROUP_ID, 'SHOP_MANAGER'),
            max_process_workers=int(os.getenv(MAX_PROCESS_WORKERS, 3)),
            mongo_host=mongo_host,
            mongo_port=mongo_port,
            mongo_username=mongo_username,
            mongo_password=mongo_password,
            mongo_database="VqaSchema"
        )
        self.default_api_route_prefix = ""
        self.routing_path = os.getenv(ROUTING, "routing.json")
