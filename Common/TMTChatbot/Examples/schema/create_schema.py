from TMTChatbot.Schema.config.schema_config import BaseSchemaConfig
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.storage.mongo_client import MongoConnector


if __name__ == "__main__":
    import json

    _config = Config()
    storage = MongoConnector(_config)

    schema_data = json.load(open("Schema/examples/schema.json", "r", encoding="utf8"))
    for schema in schema_data:
        object_config = BaseSchemaConfig(data=schema)
        storage.store_schema(object_config)
