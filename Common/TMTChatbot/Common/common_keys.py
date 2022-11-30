DEVICE = "DEVICE"
BATCH_SIZE = "BATCH_SIZE"

MONGO_HOST = "MONGO_HOST"
MONGO_PORT = "MONGO_PORT"
MONGO_USERNAME = "MONGO_USERNAME"
MONGO_PASSWORD = "MONGO_PASSWORD"
MONGO_DATABASE = "MONGO_DATABASE"

KAFKA_CONSUME_TOPIC = "KAFKA_CONSUME_TOPIC"
KAFKA_PUBLISH_TOPIC = "KAFKA_PUBLISH_TOPIC"
KAFKA_BOOTSTRAP_SERVERS = "KAFKA_BOOTSTRAP_SERVERS"
KAFKA_AUTO_OFFSET_RESET = "KAFKA_AUTO_OFFSET_RESET"
KAFKA_GROUP_ID = "KAFKA_GROUP_ID"

INTENT_URL = "INTENT_URL"
MULTIPLE_CHOICE_URL = "MULTIPLE_CHOICE_URL"
GRAPH_QA_URL = "GRAPH_QA_URL"
DOC_QA_URL = "DOC_QA_URL"
NER_URL = "NER_URL"
NODE_SEARCH_URL = "NODE_SEARCH_URL"
CONV_CONFIG_PATH = "CONV_CONFIG_PATH"
ADDRESS_URL = "ADDRESS_URL"
BILL_GENERATION_SERVICE_URL = "BILL_GENERATION_SERVICE_URL"
SIZE_PREDICTION_URL = "SIZE_PREDICTION_URL"

API_PORT = "API_PORT"
NUM_RETRY = "NUM_RETRY"
EXTERNAL_FAILED_TIMEOUT = "EXTERNAL_FAILED_TIMEOUT"
MAX_RAM_CACHE_SIZE = "MAX_RAM_CACHE_SIZE"
MAX_PROCESS_WORKERS = "MAX_PROCESS_WORKERS"
LOGGING_FILE_NAME = "LOGGING_FILE_NAME"
CACHE_HOST = "CACHE_HOST"
CACHE_PORT = "CACHE_PORT"
CACHE_TYPE = "CACHE_TYPE"
CACHE_ENDPOINT = "CACHE_ENDPOINT"
CACHE_ENDPOINT_TYPE = "CACHE_ENDPOINT_TYPE"
USE_PROCESS = "USE_PROCESS"

INPUT_BUFFER = "INPUT_BUFFER"
OUTPUT_BUFFER = "OUTPUT_BUFFER"

BEGIN = "begin"
END = "end"
LABEL = "label"
TEXT = "text"

NODES = "nodes"
NODE_ALIASES = "aliases"
NODE_ALIAS = "alias"
NODE_CHILDREN = "children"
NODE_PARENT = "parent"
NODE_PARENT_ID = "parent_id"
NODE_DATA_TYPE = "date_type"
NODE_CLASS = "class"
NODE_PARENT_CLASS = "parent_class"
NODE_ATTRIBUTES = "attributes"
NODE_IN_RELS = "node_in_rels"
NODE_OUT_RELS = "node_out_rels"
NODE_IMAGE_URLS = "image_urls"
NODE_IMAGE_FEATURES = "image_features"
REL_SRC = "rel_src"
REL_DST = "rel_dst"
REL_TYPE = "data_type"
REL_WORDS = "words"
REL_CLASS = "class"
REL_SCORE = "score"
RELATIONS = "relations"
PROP_SENTENCES = "prop_sentences"
REL_MENTIONED_TIME = "mentioned_time"

CONV_ID = "conv_id"
CONV_USER = "user"
CONV_SHOP = "shop"
CONV_STATES = "states"
CONV_DATA = "data"
CONV_HISTORY = "history"
CONV_MEMORY = "memory"
CONV_MEMORY_ID = "memory"
CONV_STATE_OBJECTS = "current_objects"
CONV_STATE_ACTIONS = "current_actions"
CONV_STATE_ACTION_CONFIG = "state_action_config"
CONV_STATE_INTENTS = "intents"
CONV_STATE_DIRECT_SEND = "direct_send"
CONV_MESSAGE = "message"
CONV_RESPONSE = "response"
CONV_LAST_RESPONSE = "last_response"
CONV_MESSAGE_ID = "message_id"
CONV_MESSAGE_USER_ID = "user_id"
CONV_MESSAGE_SHOP_ID = "shop_id"
CONV_MESSAGE_TEXT = "message"
CONV_MESSAGE_INTENT = "intents"
CONV_MESSAGE_ENTITIES = "entities"
CONV_MESSAGE_DEPENDENCY = "dependency"
CONV_MESSAGE_TIME = "created_time"
CONV_MESSAGE_MULTIPLE_CHOICES = "multiple_choices"
CONV_PENDING_MESSAGES = "pending_messages"
CONV_MESSAGE_URLS = "urls"
CONV_MESSAGE_ANSWER_INFO = "answer_info"
CONV_MESSAGE_BASE64_IMG = "base64_img"
CONV_MESSAGE_ATTACHMENTS = "attachments"
CONV_MESSAGE_ATTACHMENT_TYPE = "type"

CONV_EXPECTED_INTENTS = "intents"
CONV_BOT_POST_ACTIONS = "post_actions"
CONV_ACTION_BOT_PRE_ACTIONS = "pre_actions"
CONV_ACTION_BOT_POST_ACTIONS = "post_actions"
CONV_EXPECTED_INTENT = "schema"
CONV_EXPECTED_INTENT_DONE = "done"
CONV_EXPECTED_VALUES = "values"
CONV_EXPECTED_VALUE_SCHEMA = "schema"
CONV_EXPECTED_VALUE_DONE = "done"
CONV_RESPONSES = "responses"
CONV_NEXT_ACTIONS = "next_actions"

CONV_ACTION_NAME = "name"
CONV_ACTION_IN_CONDITION = "in_conditions"
CONV_ACTION_REQUESTS = "requests"
CONV_ACTION_RECOMMENDATIONS = "recommendations"
CONV_ACTION_EXPECTATIONS = "expectations"
CONV_ACTION_BRANCHES = "branches"
CONV_ACTION_REQUIRED = "required"
CONV_ACTION_PASSABLE = "passable"

CONV_STATE_EP = "entry_points"
CONV_STATE_EP_TAG = "tag"
CONV_STATE_EP_RESPONSES = "responses"
CONV_STATE_EP_ACTIONS = "actions"
CONV_STATE_EP_IS_GLOBAL = "is_global"

CONV_STATE_MAPPING = "mapping"
CONV_STATE_TASKS = "tasks"
CONV_STATE_EXPECTATIONS = "expectations"
CONV_STATE_BRANCHES = "branches"
CONV_STATE_MULTIPLE_CHOICES = "multiple_choices"

CONV_SCRIPT_EP = "entry_points"
CONV_SCRIPT_EP_TAG = "tag"
CONV_SCRIPT_EP_ACTIONS = "actions"

CONV_SCRIPT_CONFIG = "script_config"
CONV_SCRIPT_MAPPING = "mapping"
CONV_SCRIPT_TASKS = "tasks"
CONV_SCRIPT_EXPECTATIONS = "expectations"

SIZE_TABLE = "size_table"
ATTRIBUTES = "attributes"
USER_REQUIRED_ATTRIBUTES = "user_required_attributes"
REQUIRED_ATTRIBUTES = "required_attributes"
VARIANT_ATTRIBUTES = "variant_attributes"
CLASS = "class"
KEY_WORDS = "key_words"
PARENT_CLASS = "parent_class"
UPDATED_TIME = "updated_time"
OBJECT_ID = "id"
MONGO_OBJECT_ID = "_id"
STORAGE_ID = "storage_id"
OBJECT_HASHED = "hashed"
ENABLE = "enable"
NAME = "name"
CODE = "code"
MENTIONED_TIMES = "mentioned_times"
SCHEMA = "schema"
SHOWROOM = "showroom"

BILL_USER = "user"
BILL_SHOP = "shop"
BILL_CODE = "code"
BILL_PRODUCTS = "products"
BILL_SELECTED_CHILDREN = "selected_children"
BILL_STATUS = "status"
BILL_ORDER_STATUS = "order_status"
BILL_CREATED_TIME = "created_time"
BILL_CONFIRMED_TIME = "confirmed_time"
BILL_ADDRESS = "address"
BILL_PHONE_NUMBER = "phone_number"
BILL_NUMBER_PRODUCTS = "number"
BILL_PRICE = "price"
BILL_PAYMENT = "payment"
BILL_PAYMENT_STATUS = "payment_status"
BILL_BANK_ACCOUNT = "bank_account"
BILL_RECEIVE_TIME = "receiving_time"
BILL_RECEIVE_METHOD = "receiving_method"
BILL_RECEIVE_SHOWROOM = "receiving_showroom"
BILL_PAYMENT_METHOD = "payment_method"

USER_HISTORY_PRODUCTS = "history_products"

BANK_ACCOUNTS = "bank_accounts"
BANK_ACCOUNT_OWNER = "owner"
BANK_ACCOUNT_BANK = "bank"
BANK_ACCOUNT_NUMBER = "number"
BANK_VERIFICATION_METHOD = "verification_method"

# PRODUCT SEARCH
CROP_MODEL_PATH = "CROP_MODEL_PATH"
CROP_CONF = "CROP_CONF"
CLOTH_MODEL_PATH = "CLOTH_MODEL_PATH"
THRESHOLD_CLOTH_MODEL = "THRESHOLD_CLOTH_MODEL"
IP_ADDRESS = "IP_ADDRESS"
PORT = "PORT"
IMAGE_URL = "image_url"
TITLE = "title"
SUBTITLE = "subtitle"
JSON_DATA = "json_data"

ID_PRODUCT = "id_product"
PRODUCT_NAME = "name"
PRODUCT_FEATURES = "features"
PRODUCT_PRICE = "price"
PRODUCT_CURRENT_PRICE = "current_price"
PRODUCT_SIZE = "size"

ID = "_id"
DISTANCE = "distance"
UPDATE_DB = "update_db"
NODE_IMAGE_SEARCH_URL = "NODE_IMAGE_SEARCH_URL"
BILL_IMAGE_SERVICE_URL = "BILL_IMAGE_SERVICE_URL"
WEATHER_URL = "WEATHER_URL"
INPUT_TYPE = "input_type"
MONEY = "money"
CHECK_INPUT_DATA = "check_input_data"
LIST_RECOMMEND_ITEMS = "list_recommend_items"

# Weather
LOCATION = "location"
ADDRESS = "address"
DATE = "date"
WEATHER = "weather"

# Recommendation
NUM_RECOMMENDATIONS = "NUM_RECOMMENDATIONS"

# User
GENDER = "gender"
DEFAULT = "default"

# Shop Branch
SHOP_BRANCH = "branches"
BRANCH_WORKING_TIME = "working_time"
BRANCH_ADDRESS = "address"
BRANCH_PHONE_NUMBER = "phone_number"
MAIN_BRANCH = "main_branch"

# Policy
POLICIES = "policies"
