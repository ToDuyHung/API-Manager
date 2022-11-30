import os

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.singleton import BaseSingleton


class Config(BaseSingleton):
    def __init__(self,
                 mongo_host: str = None,
                 mongo_port: int = None,
                 mongo_username: str = None,
                 mongo_password: str = None,
                 mongo_database: str = None,
                 kafka_consume_topic: str = None,
                 kafka_publish_topic: str = None,
                 kafka_bootstrap_servers: str = None,
                 kafka_auto_offset_reset: str = None,
                 kafka_group_id: str = None,
                 api_port: int = None,
                 num_try: int = None,
                 external_failed_timeout: int = None,
                 max_ram_cache_size: int = None,
                 max_process_workers: int = None,
                 logging_folder: str = None,
                 log_name: str = None,
                 cache_host: str = None,
                 cache_port: str = None,
                 cache_endpoint: str = None,
                 cache_type: str = None,
                 cache_endpoint_type: str = None,
                 graph_qa_url: str = None,
                 doc_qa_url: str = None,
                 intent_url: str = None,
                 ner_url: str = None,
                 node_search_url: str = None,
                 node_image_search_url: str = None,
                 bill_image_service_url: str = None,
                 address_url: str = None,
                 response_delimiter: str = None,
                 multiple_choice_url: str = None,
                 weather_url: str = None,
                 bill_generation_url: str = None,
                 size_prediction_url: str = None,
                 default_api_route_prefix: str = "/process"
                 ):
        self.default_api_route_prefix = default_api_route_prefix
        self.mongo_host = mongo_host if mongo_host is not None else os.getenv(MONGO_HOST)
        mongo_port = mongo_port if mongo_port is not None else os.getenv(MONGO_PORT)
        self.mongo_port = int(mongo_port) if (mongo_port is not None and mongo_port != "") else None
        self.mongo_username = mongo_username if mongo_username is not None else os.getenv(MONGO_USERNAME)
        self.mongo_password = mongo_password if mongo_password is not None else os.getenv(MONGO_PASSWORD)
        if self.mongo_port is None or mongo_port == "":
            self.mongo_uri = f"mongodb+srv://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}/?ssl=false"
        else:
            self.mongo_uri = None

        self.mongo_database = mongo_database \
            if mongo_database is not None else os.getenv(MONGO_DATABASE, "conversation")

        self.kafka_consume_topic = kafka_consume_topic \
            if kafka_consume_topic is not None else os.getenv(KAFKA_CONSUME_TOPIC, 'baseService.test')
        self.kafka_publish_topic = kafka_publish_topic \
            if kafka_publish_topic is not None else os.getenv(KAFKA_PUBLISH_TOPIC, 'baseService')
        self.kafka_bootstrap_servers = kafka_bootstrap_servers \
            if kafka_bootstrap_servers is not None else os.getenv(KAFKA_BOOTSTRAP_SERVERS, '172.29.13.24:35000')
        self.kafka_auto_offset_reset = kafka_auto_offset_reset \
            if kafka_auto_offset_reset is not None else os.getenv(KAFKA_AUTO_OFFSET_RESET, 'earliest')
        self.kafka_group_id = kafka_group_id \
            if kafka_group_id is not None else os.getenv(KAFKA_GROUP_ID, 'baseService')

        self.api_host = "0.0.0.0"
        self.api_port = api_port if api_port is not None else int(os.getenv(API_PORT, 8080))

        self.num_retry = num_try if num_try is not None else int(os.getenv(NUM_RETRY, 5))
        self.external_failed_timeout = external_failed_timeout \
            if external_failed_timeout is not None else int(os.getenv(EXTERNAL_FAILED_TIMEOUT, 1))
        self.max_ram_cache_size = max_ram_cache_size \
            if max_ram_cache_size is not None else int(os.getenv(MAX_RAM_CACHE_SIZE, 0))
        self.max_process_workers = max_process_workers \
            if max_process_workers is not None else int(os.getenv(MAX_PROCESS_WORKERS, 3))

        self.logging_folder = logging_folder if logging_folder is not None else "logs"
        self.log_name = log_name if log_name is not None else os.getenv(LOGGING_FILE_NAME, "app.log")
        self.cache_host = cache_host if cache_host is not None else os.getenv(CACHE_HOST)
        self.cache_port = cache_port if cache_port is not None else os.getenv(CACHE_PORT)
        self.cache_endpoint = cache_endpoint \
            if cache_endpoint is not None else os.getenv(CACHE_ENDPOINT, "getdata")
        self.cache_endpoint_type = cache_endpoint_type \
            if cache_endpoint_type is not None else os.getenv(CACHE_ENDPOINT_TYPE, "socket")
        self.cache_type = cache_type if cache_type is not None else os.getenv(CACHE_TYPE, "LRU")
        self.graph_qa_url = graph_qa_url if graph_qa_url is not None else os.getenv(GRAPH_QA_URL)
        self.doc_qa_url = doc_qa_url if doc_qa_url is not None else os.getenv(DOC_QA_URL)
        self.intent_url = intent_url if intent_url is not None else os.getenv(INTENT_URL)
        self.multiple_choice_url = multiple_choice_url if multiple_choice_url is not None else os.getenv(
            MULTIPLE_CHOICE_URL)
        self.ner_url = ner_url if ner_url is not None else os.getenv(NER_URL)
        self.node_search_url = node_search_url if node_search_url is not None else os.getenv(NODE_SEARCH_URL)
        self.address_url = address_url if address_url is not None else os.getenv(ADDRESS_URL)
        self.response_delimiter = response_delimiter if response_delimiter is not None else "*"

        self.device = os.getenv(DEVICE, "cpu")
        self.crop_conf = float(os.getenv(CROP_CONF, 0.92))
        self.crop_model_path = os.getenv(CROP_MODEL_PATH, "/model/checkpoints/yolov5/yolov5s.pt")
        self.cloth_model_path = os.getenv(CLOTH_MODEL_PATH, "/model/checkpoints/cloth_model")
        self.threshold_cloth_model = float(os.getenv(THRESHOLD_CLOTH_MODEL, 0.91))
        self.ip_address = os.getenv(IP_ADDRESS, "0.0.0.0")
        self.port = int(os.getenv(PORT, 8080))
        self.node_image_search_url = node_image_search_url if \
            node_image_search_url is not None else os.getenv(NODE_IMAGE_SEARCH_URL)
        self.bill_image_service_url = bill_image_service_url if \
            bill_image_service_url is not None else os.getenv(BILL_IMAGE_SERVICE_URL)
        self.weather_url = weather_url if weather_url is not None else os.getenv(WEATHER_URL)
        self.bill_generation_url = bill_generation_url \
            if bill_generation_url is not None else os.getenv(BILL_GENERATION_SERVICE_URL)
        self.size_prediction_url = size_prediction_url \
            if size_prediction_url is not None else os.getenv(SIZE_PREDICTION_URL)
        self.num_recommendation = int(os.getenv(NUM_RECOMMENDATIONS, 3))
